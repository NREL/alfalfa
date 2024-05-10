import os
import socket
from datetime import datetime, timedelta
from time import sleep, time

import mlep

from alfalfa_worker.jobs.openstudio.lib.variables import Variables
from alfalfa_worker.jobs.step_run_base import StepRunBase
from alfalfa_worker.lib.job import (
    JobException,
    JobExceptionExternalProcess,
    message
)


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
        self.ep.bcvtbDir = '/alfalfa/bcvtb/'
        self.ep.env = {'BCVTB_HOME': '/alfalfa/bcvtb'}
        self.ep.accept_timeout = 5000  # The number of milliseconds to wait every time we attempt to connect to e+
        self.ep.mapping = os.path.realpath(self.dir / 'simulation' / 'haystack_report_mapping.json')
        self.ep.workDir = os.path.split(self.idf_file)[0]
        self.ep.arguments = (self.idf_file, self.weather_file)
        self.ep.kStep = 1  # simulation step indexed at 1
        self.ep.deltaT = 60  # the simulation step size represented in seconds - on 'step', the model will advance 1min

        # Parse variables after Haystack measure
        self.variables_file = os.path.realpath(self.dir / 'simulation' / 'variables.cfg')
        self.haystack_json_file = os.path.realpath(self.dir / 'simulation' / 'haystack_report_haystack.json')
        self.variables = Variables(self.run)

        # Define MLEP inputs
        self.ep.inputs = [0] * (self.variables.get_num_inputs())

        # The idf RunPeriod is manipulated in order to get close to the desired start time,
        # but we can only get within 24 hours. We use "bypass" steps to quickly get to the
        # exact right start time. This flag indicates we are iterating in bypass mode
        # it will be set to False once the desired start time is reach
        self.master_enable_bypass = True
        self.first_timestep = True
        # Job will wait this number of seconds for an energyplus model to start before throwing an error
        self.model_start_timeout = 300

    def time_per_step(self):
        return timedelta(seconds=3600.0 / self.time_steps_per_hour)

    def check_simulation_stop_conditions(self) -> bool:
        if self.ep.status != 0:
            return True
        if not self.ep.is_running:
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

        start_time = time()

        while time() < start_time + self.model_start_timeout and not self.ep.is_running:
            self.check_error_log()

            try:
                [self.ep.status, self.ep.msg] = self.ep.accept_socket()
            except socket.timeout:
                pass

        if not self.ep.is_running:
            raise JobExceptionExternalProcess('Timedout waiting for EnergyPlus')

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

        current_ep_time = self.get_sim_time()
        self.logger.info(
            'current_ep_time: {}, start_datetime: {}'.format(current_ep_time, self.start_datetime))
        while True:
            current_ep_time = self.get_sim_time()
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
        self.check_error_log()
        packet = self.ep.read()

        _flag, _, outputs = mlep.mlep_decode_packet(packet)
        if _flag == -1:
            self.check_error_log()
            raise JobExceptionExternalProcess("EnergyPlus experienced unknown error")
        elif _flag == -10:
            self.check_error_log()
            raise JobExceptionExternalProcess("EnergyPlus experienced initialization error")
        elif _flag == -20:
            self.check_error_log()
            raise JobExceptionExternalProcess("EnergyPlus experienced time integration error")

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
        self.first_timestep = False

        # After Step
        self.update_outputs_from_ep()

    def update_db(self):
        """
        Update database with current ep outputs and simulation time
        """
        self.write_outputs_to_redis()

        if self.historian_enabled:
            self.write_outputs_to_influx()
        self.update_sim_time_in_mongo()

    def get_sim_time(self):
        """
        Return the current time in EnergyPlus

        :return:
        :rtype datetime()
        """
        month_index = self.variables.month_index
        day_index = self.variables.day_index
        hour_index = self.variables.hour_index
        minute_index = self.variables.minute_index

        day = int(round(self.ep.outputs[day_index]))
        hour = int(round(self.ep.outputs[hour_index]))
        minute = int(round(self.ep.outputs[minute_index]))
        month = int(round(self.ep.outputs[month_index]))
        year = self.start_datetime.year

        sim_time = datetime(year, month, day, 0, 0)

        if minute == 60 and hour == 23:
            # The first timestep of simulation will have the incorrect day
            if self.first_timestep:
                hour = 0
            else:
                hour += 1

        elif minute == 60 and hour != 23:
            hour += 1

        return sim_time + timedelta(hours=hour, minutes=minute % 60)

    def replace_timestep_and_run_period_idf_settings(self):

        try:
            runperiod_str = f"""
RunPeriod,
  Alfalfa Run Period,
  {self.start_datetime.month},            !- Begin Month
  {self.start_datetime.day},              !- Begin Day of Month
  {self.start_datetime.year},             !- Begin Year
  {self.end_datetime.month},              !- End Month
  {self.end_datetime.day},                !- End Day of Month
  {self.end_datetime.year},               !- End Year
  {self.start_datetime.strftime("%A")},    !- Day of Week for Start Day
  ,                                       !- Use Weather File Holidays and Special Days
  ,                                       !- Use Weather File Daylight Saving Period
  ,                                       !- Apply Weekend Holiday Rule
  ,                                       !- Use Weather File Rain Indicators
  ,                                       !- Use Weather File Snow Indicators
  ,                                       !- Treat Weather as Actual
  ;                                       !- First Hour Interpolation Starting Values"""

            timestep_str = f"""
Timestep,
  {self.time_steps_per_hour}; !- Number of Timesteps per Hour"""

            with self.idf_file.open("a") as idf_file:
                idf_file.write(runperiod_str)
                idf_file.write(timestep_str)
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
        """Read the write arrays from redis and format them correctly to pass
        to the EnergyPlus simulation.

        Returns:
            tuple: list of inputs to set
        """
        # master_index = self.variables.input_index_from_variable_name("MasterEnable")
        # if self.master_enable_bypass:
        #     self.ep.inputs[master_index] = 0
        # else:
        self.ep.inputs = [0] * (self.variables.get_num_inputs())
        # self.ep.inputs[master_index] = 1

        for point in self.run.input_points:
            value = point.value
            index = self.variables.get_input_index(point.ref_id)
            if index == -1:
                self.logger.error('bad input index for: %s' % point.ref_id)
            elif value is None:
                if self.variables.has_enable(point.ref_id):
                    self.ep.inputs[self.variables.get_input_enable_index(point.ref_id)] = 0
            else:
                self.ep.inputs[index] = value
                if self.variables.has_enable(point.ref_id):
                    self.ep.inputs[self.variables.get_input_enable_index(point.ref_id)] = 1

        # Convert to tuple
        inputs = tuple(self.ep.inputs)
        return inputs

    def write_outputs_to_redis(self):
        """Placeholder for updating the current values exposed through Redis AFTER a simulation timestep"""
        for point in self.run.output_points:
            output_index = self.variables.get_output_index(point.ref_id)
            if output_index == -1:
                self.logger.error('bad output index for: %s' % (point.ref_id))
            else:
                output_value = self.ep.outputs[output_index]

                point.value = output_value

    def update_sim_time_in_mongo(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""
        output_time_string = "s:" + str(self.get_sim_time())
        self.logger.info(f"updating db time to: {output_time_string}")
        self.set_run_time(self.get_sim_time())

    def write_outputs_to_influx(self):
        """
        Write output data to influx
        :return:
        """
        json_body = []
        base = {
            "measurement": self.run.ref_id,
            "time": f"{self.get_sim_time()}",
        }
        response = False
        for output_point in self.run.output_points:
            output_id = output_point.ref_id
            output_index = self.variables.get_output_index(output_id)
            if output_index == -1:
                self.logger.error('bad output index for: %s' % output_id)
            else:
                output_value = self.ep.outputs[output_index]
                dis = output_point.name
                base["fields"] = {
                    "value": output_value
                }
                base["tags"] = {
                    "id": output_id,
                    "dis": dis,
                    "siteRef": self.run.ref_id,
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

    def check_error_log(self):
        mlep_logs = self.dir.glob('**/mlep.log')
        eplus_err = False
        for mlep_log in mlep_logs:
            if "===== EnergyPlus terminated with error =====" in mlep_log.read_text():
                eplus_err = True
                break
        if eplus_err:
            error_concat = ""
            error_logs = self.dir.glob('**/*.err')
            for error_log in error_logs:
                error_concat += f"{error_log}:\n"
                error_concat += error_log.read_text() + "\n"
            raise JobExceptionExternalProcess(f"Energy plus terminated with error:\n {error_concat}")

    @message
    def advance(self):
        self.logger.info(f"advance called at time {self.get_sim_time()}")
        self.step()
        self.update_db()

    @message
    def stop(self):
        super().stop()

        # Call some OpenStudio specific stop methods
        self.ep.stop(True)
        self.ep.is_running = 0

        # If E+ doesn't exit properly it can spin and delete/create files during tarring.
        # This causes an error when files that were added to the archive disappear.
        sleep(5)
