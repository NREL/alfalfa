# Standard library imports
import os
import shutil
import sys
import tarfile
import uuid
from datetime import datetime, timedelta

# Third party library imports
import mlep
import pytz

# Local imports
from alfalfa_worker.model_advancer import ModelAdvancer
from alfalfa_worker.worker_openstudio.lib.parse_variables import ParseVariables


class OSMModelAdvancer(ModelAdvancer):
    def __init__(self):
        super(OSMModelAdvancer, self).__init__()
        # Download file from bucket and extract
        self.bucket_key = os.path.join(self.parsed_path, self.tar_name)
        self.ac.s3_bucket.download_file(self.bucket_key, self.tar_path)
        tar = tarfile.open(self.tar_path)
        tar.extractall(self.sim_path)
        tar.close()

        self.time_steps_per_hour = 60  # Default to 1-min E+ step intervals (i.e. 60/hr)

        # If idf_file is named "in.idf" we need to change the name because in.idf is not accepted by mlep
        # (likely mlep is using that name internally)
        # simulation/sim.idf is the assumed convention, but sim.idf may be a symlink
        original_idf_file = os.path.join(self.sim_path_site, 'simulation/sim.idf')
        # Follow any symlink
        dst_idf_file = os.path.realpath(original_idf_file)
        self.idf_file = os.path.join(os.path.dirname(dst_idf_file), 'sim.idf')
        os.rename(dst_idf_file, self.idf_file)

        self.weather_file = os.path.realpath(os.path.join(self.sim_path_site, 'simulation/sim.epw'))
        self.str_format = "%Y-%m-%d %H:%M:%S"

        # EnergyPlus MLEP initializations
        self.ep = mlep.MlepProcess()
        self.ep.bcvtbDir = '/home/alfalfa/bcvtb/'
        self.ep.env = {'BCVTB_HOME': '/home/alfalfa/bcvtb'}
        self.ep.accept_timeout = 30000
        self.ep.mapping = os.path.realpath(os.path.join(self.sim_path_site, 'simulation/haystack_report_mapping.json'))
        self.ep.workDir = os.path.split(self.idf_file)[0]
        self.ep.arguments = (self.idf_file, self.weather_file)
        self.ep.kStep = 1  # simulation step indexed at 1
        self.ep.deltaT = 60  # the simulation step size represented in seconds - on 'step', the model will advance 1min

        # Parse variables after Haystack measure
        self.variables_file = os.path.realpath(os.path.join(self.sim_path_site, 'simulation/variables.cfg'))
        self.haystack_json_file = os.path.realpath(os.path.join(self.sim_path_site, 'simulation/haystack_report_haystack.json'))
        self.variables = ParseVariables(self.variables_file, self.ep.mapping, self.haystack_json_file)

        # Define MLEP inputs
        self.ep.inputs = [0] * ((len(self.variables.get_input_ids())) + 1)

        # The idf RunPeriod is manipulated in order to get close to the desired start time,
        # but we can only get within 24 hours. We use "bypass" steps to quickly get to the
        # exact right start time. This flag indicates we are interating in bypass mode
        # it will be set to False once the desired start time is reach
        self.master_enable_bypass = True

    def seconds_per_time_step(self):
        return 3600.0 / self.time_steps_per_hour

    def check_stop_conditions(self):
        """Placeholder to check for all stopping conditions"""
        self.check_sim_status_stop()
        if self.ep.status != 0:
            self.stop = True
        if not self.ep.is_running:
            self.stop = True

    def init_sim(self):
        """
        Initialize EnergyPlus co-simulation.

        :return:
        """
        self.osm_idf_files_prep()
        (self.ep.status, self.ep.msg) = self.ep.start()
        if self.ep.status != 0:
            self.model_logger.logger.info('Could not start EnergyPlus: {}'.format(self.ep.msg))

        [self.ep.status, self.ep.msg] = self.ep.accept_socket()
        if self.ep.status != 0:
            self.model_logger.logger.info('Could not connect to EnergyPlus: {}'.format(self.ep.msg))

    def advance_to_start_time(self):
        """ We get near the requested start time by manipulating the idf file,
        however the idf start time is limited to the resolution of 1 day.
        The purpose of this function is to move the simulation to the requested
        start minute.
        This is accomplished by advancing the simulation as quickly as possible. Data is not
        published to database during this process
        """
        self.exchange_data()

        current_ep_time = self.get_energyplus_datetime()
        self.model_logger.logger.info(
            'current_ep_time: {}, start_datetime: {}'.format(current_ep_time, self.start_datetime))
        while True:
            current_ep_time = self.get_energyplus_datetime()
            if current_ep_time < self.start_datetime:
                self.model_logger.logger.info(
                    'current_ep_time: {}, start_datetime: {}'.format(current_ep_time, self.start_datetime))
                self.step()
            else:
                self.model_logger.logger.info(f"current_ep_time: {current_ep_time} reached desired start_datetime: {self.start_datetime}")
                break
        self.master_enable_bypass = False
        self.update_db()

    def exchange_data(self):
        """
        Write inputs to simulation and get updated outputs
        This does not advance the simulation on its own, instead
        to advance the simulation increment ep.kstep and then call this function
        See self.step
        """
        # Before step
        inputs = self.read_write_arrays_and_prep_inputs()
        self.ep.write(mlep.mlep_encode_real_data(2, 0, (self.ep.kStep - 1) * self.ep.deltaT, inputs))
        # After step
        packet = self.ep.read()
        flag, _, outputs = mlep.mlep_decode_packet(packet)
        self.ep.outputs = outputs
        return outputs

    def step(self):
        """
        Simulate one simulation timestep
        """
        self.ep.kStep += 1
        self.exchange_data()

    def update_db(self):
        """
        Update database with current ep outputs and simulation time
        """
        self.write_outputs_to_mongo()
        if self.historian_enabled:
            self.write_outputs_to_influx()
        self.update_sim_time_in_mongo()

    def create_tag_dictionaries(self):
        """Placeholder for method necessary to create Haystack entities and records"""
        # TODO maybe don't need...

    def cleanup(self):
        """
        Simulation files zipped and uploaded to s3 bucket, timeCompleted is set to now.
        Mongo records updated as follows:
        - site: simStatus set to stopped
        - all rec.cur: curVals, curError set to "", curStatus set to disabled

        :return:
        """
        sim_id = str(uuid.uuid4())
        tar_name = "%s.tar.gz" % sim_id

        tar_file = tarfile.open(tar_name, "w:gz")
        tar_file.add(self.sim_path_site, filter=self.reset, arcname=self.site_id)
        tar_file.close()

        s3_key = "simulated/%s/%s" % (self.site_id, tar_name)
        self.ac.s3_bucket.upload_file(tar_name, s3_key)

        os.remove(tar_name)
        shutil.rmtree(self.sim_path_site)

        name = self.site.get("rec", {}).get("dis", "Unknown") if self.site else "Unknown"
        name = name.replace("s:", "")
        t = str(datetime.now(tz=pytz.UTC))
        self.ac.mongo_db_sims.insert_one(
            {"_id": sim_id, "siteRef": self.site_id, "s3Key": s3_key, "name": name, "timeCompleted": t})
        self.ac.mongo_db_recs.update_one({"_id": self.site_id},
                                         {"$set": {"rec.simStatus": "s:Stopped"},
                                          "$unset": {"rec.datetime": "", "rec.step": ""}}, False)
        self.ac.mongo_db_recs.update_many({"_id": self.site_id, "rec.cur": "m:"},
                                          {"$unset": {"rec.curVal": "", "rec.curErr": ""},
                                           "$set": {"rec.curStatus": "s:disabled"}},
                                          False)
        self.ep.stop(True)
        self.ep.is_running = 0

    def run_external_clock(self):
        self.advance_to_start_time()
        while True:
            self.process_pubsub_message()

            if self.stop:
                self.cleanup()
                break

            if self.advance:
                self.step()
                self.update_db()
                self.set_redis_states_after_advance()
                self.advance = False

    def step_delta_time(self):
        """
        Return a timedelta object to represent the real time between steps
        This is used by the internal clock. Does not apply to the external clock
        """
        return timedelta(seconds=(self.seconds_per_time_step() / self.step_sim_value))

    def run_timescale(self):
        self.advance_to_start_time()

        next_step_time = datetime.now() + self.step_delta_time()
        while True:
            current_time = datetime.now()

            if current_time >= next_step_time:
                self.advance = True

            self.process_pubsub_message()

            if self.stop:
                self.cleanup()
                break

            if self.advance:
                self.step()
                self.update_db()
                self.set_redis_states_after_advance()
                next_step_time = next_step_time + self.step_delta_time()
                self.advance = False

    def reset(self, tarinfo):
        """
        TODO: Don't know what this function does...

        :param tarinfo:
        :return:
        """
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"
        return tarinfo

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

        # TODO where doe ep.outputs actually get written to...? can't find in mlep lib
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
            # then find the relavant lines by couting how many lines away from the patten.
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
            self.model_logger.logger.error('Unsuccessful in replacing values in idf file.  Exception: {}'.format(e))
            sys.exit(1)

    def copy_variables_cfg(self):
        """
        Copy the variables.cfg file from the OpenStudio Measure reports directory to the
        simulation directory

        :return:
        """
        shutil.copyfile(self.variables_file_old, self.variables_file_new)

    def osm_idf_files_prep(self):
        """
        Replace the timestep and starting and ending year, month, day, day of week in the idf file.

        :return:
        """
        self.replace_timestep_and_run_period_idf_settings()

    def process_pubsub_message(self):
        """
        Process message from pubsub and set relevant flags

        :return:
        """
        message = self.ac.redis_pubsub.get_message()
        if message:
            data = message['data']
            if data == b'advance':
                self.advance = True
            elif data == b'stop':
                self.stop = True

    def set_redis_states_after_advance(self):
        """Set an idle state in Redis"""
        self.ac.redis.publish(self.site_id, 'complete')
        self.ac.redis.hset(self.site_id, 'control', 'idle')

    def read_write_arrays_and_prep_inputs(self):
        master_index = self.variables.input_index_from_variable_name("MasterEnable")
        if self.master_enable_bypass:
            self.ep.inputs[master_index] = 0
        else:
            self.ep.inputs = [0] * ((len(self.variables.get_input_ids())) + 1)
            self.ep.inputs[master_index] = 1
            for array in self.ac.mongo_db_write_arrays.find({"siteRef": self.site_id}):
                for val in array.get('val'):
                    if val is not None:
                        index = self.variables.get_input_index(array.get('_id'))
                        if index == -1:
                            self.model_logger.logger.error('bad input index for: %s' % array.get('_id'))
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
                self.model_logger.logger.error('bad output index for: %s' % output_id)
            else:
                output_value = self.ep.outputs[output_index]

                # TODO: Make this better with a bulk update
                # Also at some point consider removing curVal and related fields after sim ends
                self.ac.mongo_db_recs.update_one({"_id": output_id}, {
                    "$set": {"rec.curVal": "n:%s" % output_value, "rec.curStatus": "s:ok",
                             "rec.cur": "m:"}}, False)

    def update_sim_time_in_mongo(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""
        output_time_string = "s:" + str(self.get_energyplus_datetime())
        self.ac.mongo_db_recs.update_one({"_id": self.site_id}, {
            "$set": {"rec.datetime": output_time_string, "rec.step": "n:" + str(self.ep.kStep),
                     "rec.simStatus": "s:Running"}}, False)

    def write_outputs_to_influx(self):
        """
        Write output data to influx
        :return:
        """
        json_body = []
        base = {
            "measurement": self.site_id,
            "time": f"{self.get_energyplus_datetime()}",
        }
        response = False
        for output_id in self.variables.get_output_ids():
            output_index = self.variables.get_output_index(output_id)
            if output_index == -1:
                self.model_logger.logger.error('bad output index for: %s' % output_id)
            else:
                output_value = self.ep.outputs[output_index]
                dis = self.variables.get_haystack_dis_given_id(output_id)
                base["fields"] = {
                    "value": output_value
                }
                base["tags"] = {
                    "id": output_id,
                    "dis": dis,
                    "siteRef": self.site_id,
                    "point": True,
                    "source": 'alfalfa'
                }
                json_body.append(base.copy())
        try:
            response = self.ac.influx_client.write_points(points=json_body,
                                                          time_precision='s',
                                                          database=self.ac.influx_db_name)

        except ConnectionError as e:
            self.model_logger.logger.error(f"Influx ConnectionError on curVal write: {e}")
        if not response:
            self.model_logger.logger.warning(f"Unsuccessful write to influx.  Response: {response}")
            self.model_logger.logger.info(f"Attempted to write: {json_body}")
        else:
            self.model_logger.logger.info(
                f"Successful write to influx.  Length of JSON: {len(json_body)}")
