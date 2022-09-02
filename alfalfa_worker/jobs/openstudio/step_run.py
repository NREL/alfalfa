import os
from datetime import datetime, timedelta
from time import sleep
from uuid import uuid4

import mlep
import pytz

from alfalfa_worker.jobs.openstudio.lib.parse_variables import ParseVariables
from alfalfa_worker.jobs.step_run_base import StepRunBase
from alfalfa_worker.lib.job import (
    JobException,
    JobExceptionExternalProcess,
    message
)
from alfalfa_worker.lib.point import Point, PointType


class StepRun(StepRunBase):
    def __init__(self, run_id, realtime, timescale, external_clock, start_datetime, end_datetime) -> None:
        self.checkout_run(run_id)
        super().__init__(run_id, realtime, timescale, external_clock, start_datetime, end_datetime)
        self.logger.info(f"{start_datetime}, {end_datetime}")
        self.time_steps_per_hour = 60  # Default to 1-min E+ step intervals (i.e. 60/hr)

        # If idf_file is named "in.idf" we need to change the name because in.idf is not accepted by mlep
        # (likely mlep is using that name internally)
        # simulation/sim.idf is the assumed convention, but sim.idf may be a symlink
        original_idf_file = self.dir / 'simulation' / 'sim.idf'
        # Follow any symlink
        dst_idf_file = original_idf_file.resolve()
        self.idf_file = dst_idf_file.parents[0] / 'sim.idf'
        dst_idf_file.rename(self.idf_file)

        self.weather_file = os.path.realpath(self.dir / 'simulation' / 'sim.epw')
        self.str_format = "%Y-%m-%d %H:%M:%S"

        # EnergyPlus MLEP initializations
        self.ep = mlep.MlepProcess()
        self.ep.bcvtbDir = '/home/alfalfa/bcvtb/'
        self.ep.env = {'BCVTB_HOME': '/home/alfalfa/bcvtb'}
        self.ep.accept_timeout = 60000
        self.ep.mapping = os.path.realpath(self.dir / 'simulation' / 'haystack_report_mapping.json')
        self.ep.workDir = os.path.split(self.idf_file)[0]
        self.ep.arguments = (self.idf_file, self.weather_file)
        self.ep.kStep = 1  # simulation step indexed at 1
        self.ep.deltaT = 60  # the simulation step size represented in seconds - on 'step', the model will advance 1min

        # Parse variables after Haystack measure
        self.variables_file = os.path.realpath(self.dir / 'simulation' / 'variables.cfg')
        self.haystack_json_file = os.path.realpath(self.dir / 'simulation' / 'haystack_report_haystack.json')
        self.variables = ParseVariables(self.variables_file, self.ep.mapping, self.haystack_json_file)

        # Define MLEP inputs
        self.ep.inputs = [0] * ((len(self.variables.get_input_ids())) + 1)

        # The idf RunPeriod is manipulated in order to get close to the desired start time,
        # but we can only get within 24 hours. We use "bypass" steps to quickly get to the
        # exact right start time. This flag indicates we are iterating in bypass mode
        # it will be set to False once the desired start time is reach
        self.master_enable_bypass = True

        self.setup_connections()

        # Store the site for later use
        self.site = self.mongo_db_recs.find_one({"_id": self.run.id})

    def time_per_step(self):
        return timedelta(seconds=3600.0 / self.time_steps_per_hour)

    def check_simulation_stop_conditions(self) -> bool:
        if self.ep.status != 0:
            return True
        if not self.ep.is_running:
            return True
        if self.get_energyplus_datetime() >= self.end_datetime:
            return True
        return False

    def init_sim(self):
        """
        Initialize EnergyPlus co-simulation.

        :return:
        """
        self.osm_idf_files_prep()
        (self.ep.status, self.ep.msg) = self.ep.start()
        if self.ep.status != 0:
            raise JobExceptionExternalProcess('Could not start EnergyPlus: {}'.format(self.ep.msg))

        [self.ep.status, self.ep.msg] = self.ep.accept_socket()
        if self.ep.status != 0:
            raise JobExceptionExternalProcess('Could not start EnergyPlus: {}'.format(self.ep.msg))

        self.set_run_time(self.start_datetime)

    def advance_to_start_time(self):
        """ We get near the requested start time by manipulating the idf file,
        however the idf start time is limited to the resolution of 1 day.
        The purpose of this function is to move the simulation to the requested
        start minute.
        This is accomplished by advancing the simulation as quickly as possible. Data is not
        published to database during this process
        """
        self.update_outputs_from_ep()

        current_ep_time = self.get_energyplus_datetime()
        self.logger.info(
            'current_ep_time: {}, start_datetime: {}'.format(current_ep_time, self.start_datetime))
        while True:
            current_ep_time = self.get_energyplus_datetime()
            if current_ep_time < self.start_datetime:
                self.logger.info(
                    'current_ep_time: {}, start_datetime: {}'.format(current_ep_time, self.start_datetime))
                self.step()
            else:
                self.logger.info(f"current_ep_time: {current_ep_time} reached desired start_datetime: {self.start_datetime}")
                break
        self.master_enable_bypass = False
        self.update_db()

    def update_outputs_from_ep(self):
        """Reads outputs from E+ step"""
        packet = self.ep.read()
        flag, _, outputs = mlep.mlep_decode_packet(packet)
        self.ep.outputs = outputs

    def step(self):
        """
        Write inputs to simulation and get updated outputs.
        This will advance the simulation one timestep.
        """

        # This doesn't really do anything. Energyplus does not check the timestep value coming from the external interface
        self.ep.kStep += 1
        # Begin Step
        inputs = self.read_write_arrays_and_prep_inputs()
        # Send packet to E+ via ExternalInterface Socket.
        # Any writes to this socket trigger a model advance.
        # First Arg: "2" - The version of the communication protocol
        # Second Arg: "0" - The communication flag, 0 means normal communication
        # Third Arg: "(self.ep.kStep - 1) * self.ep.deltaT" - The simulation time, this isn't actually checked or used on the E+ side
        packet = mlep.mlep_encode_real_data(2, 0, (self.ep.kStep - 1) * self.ep.deltaT, inputs)
        self.ep.write(packet)

        # After Step
        self.update_outputs_from_ep()

    def update_db(self):
        """
        Update database with current ep outputs and simulation time
        """
        self.write_outputs_to_mongo()
        if self.historian_enabled:
            self.write_outputs_to_influx()
        self.update_sim_time_in_mongo()

    def get_energyplus_datetime(self):
        """
        Return the current time in EnergyPlus

        :return:
        :rtype datetime()
        """
        month_index = self.variables.output_index_from_type_and_name("current_month", "EMS")
        day_index = self.variables.output_index_from_type_and_name("current_day", "EMS")
        hour_index = self.variables.output_index_from_type_and_name("current_hour", "EMS")
        minute_index = self.variables.output_index_from_type_and_name("current_minute", "EMS")

        day = int(round(self.ep.outputs[day_index]))
        hour = int(round(self.ep.outputs[hour_index]))
        minute = int(round(self.ep.outputs[minute_index]))
        month = int(round(self.ep.outputs[month_index]))
        year = self.start_datetime.year

        if minute == 60 and hour == 23:
            hour = 0
            minute = 0
        elif minute == 60 and hour != 23:
            hour = hour + 1
            minute = 0

        return datetime(year, month, day, hour, minute)

    def replace_timestep_and_run_period_idf_settings(self):
        try:
            # Generate Lines
            begin_month_line = '  {},                                      !- Begin Month\n'.format(
                self.start_datetime.month)
            begin_day_line = '  {},                                      !- Begin Day of Month\n'.format(
                self.start_datetime.day)
            end_month_line = '  {},                                      !- End Month\n'.format(self.end_datetime.month)
            end_day_line = '  {},                                      !- End Day of Month\n'.format(
                self.end_datetime.day)
            time_step_line = '  {};                                      !- Number of Timesteps per Hour\n'.format(
                self.time_steps_per_hour)
            begin_year_line = '  {},                                   !- Begin Year\n'.format(self.start_datetime.year)
            end_year_line = '  {},                                   !- End Year\n'.format(self.end_datetime.year)
            dayOfweek_line = '  {},                                   !- Day of Week for Start Day\n'.format(
                self.start_datetime.strftime("%A"))
            line_timestep = None  # Sanity check to make sure object exists
            line_runperiod = None  # Sanity check to make sure object exists

            # Overwrite File
            # the basic idea is to locate the pattern first (e.g. Timestep, RunPeriod)
            # then find the relevant lines by counting how many lines away from the patten.
            count = -1
            with open(self.idf_file, 'r+') as f:
                lines = f.readlines()
                f.seek(0)
                f.truncate()
                for line in lines:
                    count = count + 1
                    if line.strip() == 'RunPeriod,':  # Equivalency statement necessary
                        line_runperiod = count
                    if line.strip() == 'Timestep,':  # Equivalency statement necessary
                        line_timestep = count + 1

                if not line_timestep:
                    raise TypeError(
                        "line_timestep cannot be None.  'Timestep,' should be present in IDF file, but is not.")

                if not line_runperiod:
                    raise TypeError(
                        "line_runperiod cannot be None.  'RunPeriod,' should be present in IDF file, but is not.")

                for i, line in enumerate(lines):
                    if (i < line_runperiod or i > line_runperiod + 12) and (i != line_timestep):
                        f.write(line)
                    elif i == line_timestep:
                        line = time_step_line
                        f.write(line)
                    else:
                        if i == line_runperiod + 2:
                            line = begin_month_line
                        elif i == line_runperiod + 3:
                            line = begin_day_line
                        elif i == line_runperiod + 4:
                            line = begin_year_line
                        elif i == line_runperiod + 5:
                            line = end_month_line
                        elif i == line_runperiod + 6:
                            line = end_day_line
                        elif i == line_runperiod + 7:
                            line = end_year_line
                        elif i == line_runperiod + 8:
                            line = dayOfweek_line
                        else:
                            line = lines[i]
                        f.write(line)
        except BaseException as e:
            self.logger.error('Unsuccessful in replacing values in idf file.  Exception: {}'.format(e))
            raise JobException('Unsuccessful in replacing values in idf file.  Exception: {}'.format(e))

    def osm_idf_files_prep(self):
        """
        Replace the timestep and starting and ending year, month, day, day of week in the idf file.

        :return:
        """
        self.replace_timestep_and_run_period_idf_settings()

    def read_write_arrays_and_prep_inputs(self):
        master_index = self.variables.input_index_from_variable_name("MasterEnable")
        if self.master_enable_bypass:
            self.ep.inputs[master_index] = 0
        else:
            self.ep.inputs = [0] * ((len(self.variables.get_input_ids())) + 1)
            self.ep.inputs[master_index] = 1
            for array in self.mongo_db_write_arrays.find({"siteRef": self.run.id}):
                for val in array.get('val'):
                    if val is not None:
                        index = self.variables.get_input_index(array.get('_id'))
                        if index == -1:
                            self.logger.error('bad input index for: %s' % array.get('_id'))
                        else:
                            self.ep.inputs[index] = val
                            self.ep.inputs[index + 1] = 1
                            break
        # Convert to tuple
        inputs = tuple(self.ep.inputs)
        return inputs

    def write_outputs_to_mongo(self):
        """Placeholder for updating the current values exposed through Mongo AFTER a simulation timestep"""
        for output_id in self.variables.get_output_ids():
            output_index = self.variables.get_output_index(output_id)
            if output_index == -1:
                self.logger.error('bad output index for: %s' % output_id)
            else:
                output_value = self.ep.outputs[output_index]

                # TODO: Make this better with a bulk update
                # Also at some point consider removing curVal and related fields after sim ends
                self.mongo_db_recs.update_one({"_id": output_id}, {
                    "$set": {"rec.curVal": "n:%s" % output_value, "rec.curStatus": "s:ok",
                             "rec.cur": "m:"}}, False)

                # Write to points
                self.run.get_point_by_key(output_id).val = output_value
                self.run_manager.update_db(self.run)

    def update_sim_time_in_mongo(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""
        output_time_string = "s:" + str(self.get_energyplus_datetime())
        self.logger.info(f"updating db time to: {output_time_string}")
        self.set_run_time(self.get_energyplus_datetime())

    def write_outputs_to_influx(self):
        """
        Write output data to influx
        :return:
        """
        json_body = []
        base = {
            "measurement": self.run.id,
            "time": f"{self.get_energyplus_datetime()}",
        }
        response = False
        for output_id in self.variables.get_output_ids():
            output_index = self.variables.get_output_index(output_id)
            if output_index == -1:
                self.logger.error('bad output index for: %s' % output_id)
            else:
                output_value = self.ep.outputs[output_index]
                dis = self.variables.get_haystack_dis_given_id(output_id)
                base["fields"] = {
                    "value": output_value
                }
                base["tags"] = {
                    "id": output_id,
                    "dis": dis,
                    "siteRef": self.run.id,
                    "point": True,
                    "source": 'alfalfa'
                }
                json_body.append(base.copy())
        try:
            response = self.influx_client.write_points(points=json_body,
                                                       time_precision='s',
                                                       database=self.influx_db_name)

        except ConnectionError as e:
            self.logger.error(f"Influx ConnectionError on curVal write: {e}")
        if not response:
            self.logger.warning(f"Unsuccessful write to influx.  Response: {response}")
            self.logger.info(f"Attempted to write: {json_body}")
        else:
            self.logger.info(
                f"Successful write to influx.  Length of JSON: {len(json_body)}")

    def setup_points(self):
        self.logger.info('setting up points')
        points = []
        for output_id in self.variables.get_output_ids():
            output_index = self.variables.get_output_index(output_id)
            if output_index == -1:
                self.logger.error('bad output index for: %s' % output_id)
            else:
                dis = self.variables.get_haystack_dis_given_id(output_id)
                point = Point(output_id, dis, PointType.OUTPUT)
                points.append(point)

        for input_id in self.variables.get_input_ids():
            input_index = self.variables.get_input_index(input_id)
            if input_index == -1:
                self.logger.error('bad input index for: %s' % input_id)
            else:
                dis = self.variables.get_haystack_dis_given_id(input_id)
                point = Point(input_id, dis, PointType.INPUT)
                points.append(point)

        self.add_points(points)

    @message
    def advance(self):
        self.logger.info(f"advance called at time {self.get_energyplus_datetime()}")
        self.step()
        self.update_db()

    @message
    def stop(self):
        super().stop()

        # DELETE
        name = self.site.get("rec", {}).get("dis", "Unknown") if self.site else "Unknown"
        name = name.replace("s:", "")
        t = str(datetime.now(tz=pytz.UTC))
        self.mongo_db_sims.insert_one(
            {"_id": str(uuid4()), "siteRef": self.run.id, "s3Key": f"run/{self.run.id}.tar.gz", "name": name, "timeCompleted": t})
        self.mongo_db_recs.update_one({"_id": self.run.id},
                                      {"$set": {"rec.simStatus": "s:Stopped"},
                                          "$unset": {"rec.datetime": "", "rec.step": ""}}, False)
        self.mongo_db_recs.update_many({"_id": self.run.id, "rec.cur": "m:"},
                                       {"$unset": {"rec.curVal": "", "rec.curErr": ""},
                                           "$set": {"rec.curStatus": "s:disabled"}},
                                       False)
        # END DELETE

        self.ep.stop(True)
        self.ep.is_running = 0

        # If E+ doesn't exit properly it can spin and delete/create files during tarring.
        # This causes an error when files that were added to the archive disappear.
        sleep(5)
