import os
import traceback
from datetime import datetime, timedelta

from pyenergyplus.api import EnergyPlusAPI

from alfalfa_worker.jobs.openstudio.lib.variables import Variables
from alfalfa_worker.jobs.step_run_base import Role, StepRunBase
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

        self.variables = Variables(self.run)

        self.ep_api = EnergyPlusAPI()
        self.ep_state = self.ep_api.state_manager.new_state()
        self.ep_advance_flag = False
        self.ep_io_objects = {}

        # The idf RunPeriod is manipulated in order to get close to the desired start time,
        # but we can only get within 24 hours. We use "bypass" steps to quickly get to the
        # exact right start time. This flag indicates we are iterating in bypass mode
        # it will be set to False once the desired start time is reach
        self.first_timestep = True
        # Job will wait this number of seconds for an energyplus model to start before throwing an error
        self.model_start_timeout = 300

    def time_per_step(self):
        return timedelta(seconds=3600.0 / self.time_steps_per_hour)

    def init_sim(self):
        """
        Initialize EnergyPlus co-simulation.

        :return:
        """
        self.osm_idf_files_prep()
        self.ep_register_callbacks()
        self.ep_request_variables()

    def ep_request_variables(self):
        for point in self.variables.points.values():
            if "output" in point:
                if point["output"]["type"] == "OutputVariable":
                    self.ep_api.exchange.request_variable(self.ep_state, **point["output"]["parameters"])

    def ep_register_callbacks(self):
        self.ep_api.runtime.callback_begin_new_environment(self.ep_state,
                                                           self.ep_init_handles)
        self.ep_api.runtime.callback_end_zone_timestep_after_zone_reporting(self.ep_state,
                                                                            self.ep_begin_timestep)
        # self.ep_api.runtime.callback_begin_zone_timestep_after_init_heat_balance(self.ep_state, self.ep_write_inputs)

    def ep_init_handles(self, state):
        try:
            self.logger.info("Generating handles")

            def get_handle(type, parameters):
                self.logger.info(f"Getting handle for component of type: {type} with params: {parameters}")
                handle = None
                if type == "GlobalVariable":
                    handle = self.ep_api.exchange.get_global_handle(state, **parameters)
                elif type == "InternalVariable":
                    handle = self.ep_api.exchange.get_internal_variable_handle(state, **parameters)
                elif type == "OutputVariable":
                    handle = self.ep_api.exchange.get_variable_handle(state, **parameters)
                    self.logger.info(f"Got handle: {handle} for {parameters}")
                elif type == "Meter":
                    handle = self.ep_api.exchange.get_meter_handle(state, **parameters)
                elif type == "Actuator":
                    handle = self.ep_api.exchange.get_actuator_handle(state, **parameters)
                else:
                    self.logger.error(f"Unknown point type: {type}")
                    raise JobException(f"Unknown point type: {type}")
                if handle == -1:
                    self.logger.error(f"Handle not found for point of type: {type} and parameters: {parameters}")
                    raise JobException(f"Handle not found for point of type: {type} and parameters: {parameters}")
                return handle
            self.logger.info("Iterating through points")
            self.logger.info(f"{len(self.variables.points)} point found")
            for id, point in self.variables.points.items():
                self.logger.info(f"getting handle for id: {id}")
                if "input" in point:
                    self.variables.points[id]["input"]["handle"] = get_handle(**point["input"])
                if "output" in point:
                    self.variables.points[id]["output"]["handle"] = get_handle(**point["output"])
        except Exception as e:
            self.ep_api.runtime.stop_simulation(state)
            self.ep_api.runtime.issue_severe(state, str(e))
            self.ep_api.runtime.issue_severe(state, str(traceback.format_exc()))
            raise e

    def ep_begin_timestep(self, state):
        try:
            warmup = self.ep_api.exchange.warmup_flag(state)
            kind_of_sim = self.ep_api.exchange.kind_of_sim(state)
            if warmup or kind_of_sim == 1:
                return
            self.ep_read_outputs(state)
            self.set_run_time(self.get_sim_time(state))
            self.wait_for_advance()
            self.ep_write_inputs(state)
            if not self.is_running:
                self.ep_api.runtime.stop_simulation(state)
        except Exception as e:
            self.ep_api.runtime.stop_simulation(state)
            self.ep_api.runtime.issue_severe(state, str(e))
            self.ep_api.runtime.issue_severe(state, str(traceback.format_exc()))
            raise e

    def ep_read_outputs(self, state):
        """Reads outputs from E+ state"""
        influx_points = []
        for point in self.run.output_points:
            handle = self.variables.points[point.ref_id]["output"]["handle"]
            type = self.variables.points[point.ref_id]["output"]["type"]
            value = None
            if type == "GlobalVariable":
                value = self.ep_api.exchange.get_variable_value(state, handle)
            elif type == "InternalVariable":
                value = self.ep_api.exchange.get_internal_variable_value(state, handle)
            elif type == "OutputVariable":
                value = self.ep_api.exchange.get_global_value(state, handle)
            elif type == "Meter":
                value = self.ep_api.exchange.get_meter_value(state, handle)
            elif type == "Actuator":
                value = self.ep_api.exchange.get_actuator_value(state, handle)
            else:
                raise JobException(f"Unknown point type: {type}")
            point.value = value
            if self.historian_enabled:
                influx_points.append({
                    "measurement": self.run.ref_id,
                    "time": self.run.sim_time,
                    "value": value,
                    "id": point.ref_id,
                    "point": True,
                    "source": "alfalfa"
                })
        if self.historian_enabled:
            try:
                response = self.influx_client.write_points(points=influx_points,
                                                           time_precision='s',
                                                           database=self.influx_db_name)
            except ConnectionError as e:
                self.logger.error(f"Influx ConnectionError on curVal write: {e}")
            if not response:
                self.logger.warning(f"Unsuccessful write to influx.  Response: {response}")
                self.logger.info(f"Attempted to write: {influx_points}")
            else:
                self.logger.info(
                    f"Successful write to influx.  Length of JSON: {len(influx_points)}")

    def ep_write_inputs(self):
        """Writes inputs to E+ state"""
        for point in self.run.input_points:
            handle = self.variables.points[point.ref_id]["input"]["handle"]
            type = self.variables.points[point.ref_id]["input"]["type"]
            if type == "GlobalVariable":
                self.ep_api.exchange.set_global_value(self.ep_state, handle, point.value)
            if type == "Actuator":
                if point.value is not None:
                    self.ep_api.exchange.set_actuator_value(self.ep_state, handle, point.value)
                else:
                    # TODO Don't reset the actuator if we already reset it.
                    self.ep_api.exchange.reset_actuator(self.ep_api, handle)

    def start_sim_executive(self):
        return_code = self.ep_api.runtime.run_energyplus(state=self.ep_state, command_line_args=['-w', str(self.weather_file), '-d', str(self.dir / 'simulation'), '-r', str(self.idf_file)])
        if return_code != 0:
            self.check_error_log()

    def setup_points(self):
        self.logger.info("Generating Points")
        self.variables.generate_points()

    @property
    def role(self):
        return Role.FOLLOWER

    def get_sim_time(self, state):
        """
        Return the current time in EnergyPlus

        :return:
        :rtype datetime()
        """

        day = self.ep_api.exchange.day_of_month(state)
        hour = self.ep_api.exchange.hour(state)
        minute = self.ep_api.exchange.minutes(state)
        month = self.ep_api.exchange.month(state)
        year = self.ep_api.exchange.year(state)

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

    def update_sim_time_in_mongo(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""
        sim_time = self.get_sim_time()
        self.logger.info(f"updating db time to: {sim_time}")
        self.set_run_time(sim_time)

    def check_error_log(self):
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
