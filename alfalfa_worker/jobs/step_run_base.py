import datetime
import os

from influxdb import InfluxDBClient

from alfalfa_worker.lib.job import (
    Job,
    JobException,
    JobExceptionSimulation,
    message
)
from alfalfa_worker.lib.run import RunStatus


class StepRunBase(Job):
    def __init__(self, run_id, realtime, timescale, external_clock, start_datetime, end_datetime) -> None:
        super().__init__()
        self.set_run_status(RunStatus.STARTING)
        self.step_sim_type, self.step_sim_value, self.start_datetime, self.end_datetime = self.process_inputs(realtime, timescale, external_clock, start_datetime, end_datetime)
        self.logger.info(f"sim_type is {self.step_sim_type}")
        if self.step_sim_type == 'timescale':
            self.step_sim_value = self.step_sim_value
        elif self.step_sim_type == 'realtime':
            self.step_sim_value = 1
        else:
            self.step_sim_value = 5

        self.start_datetime = datetime.datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
        self.end_datetime = datetime.datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S')

        self.historian_enabled = os.environ.get('HISTORIAN_ENABLE', False) == 'true'

        self.first_step_warmup = False
        self.set_run_status(RunStatus.STARTED)

    def process_inputs(self, realtime, timescale, external_clock, start_datetime, end_datetime):
        # TODO change server side message: startDatetime to start_datetime
        timescale = False if timescale == 'undefined' else timescale

        # make sure the inputs are typed correctly
        try:
            timescale = int(timescale)
        except ValueError:
            self.logger.info(f"timescale is not an integer, continuing as sim_type=timescale. Value was {timescale}")

        if not isinstance(realtime, bool):
            realtime = True if realtime and realtime.lower() == 'true' else False
        if not isinstance(external_clock, bool):
            external_clock = True if external_clock and external_clock.lower() == 'true' else False

        self.logger.debug(f"start_datetime type: {type(start_datetime)}\tstart_datetime: {start_datetime}")
        self.logger.debug(f"end_datetime type: {type(end_datetime)}\tend_datetime: {end_datetime}")
        self.logger.debug(f"realtime type: {type(realtime)}\trealtime: {realtime}")
        self.logger.debug(f"timescale type: {type(timescale)}\ttimescale: {timescale}")
        self.logger.debug(f"external_clock type: {type(external_clock)}\texternal_clock: {external_clock}")

        # Check for at least one of the required parameters
        if not realtime and not timescale and not external_clock:
            self.logger.error("At least one of 'external_clock', 'timescale', or 'realtime' must be specified")
            raise JobException("At least one of 'external_clock', 'timescale', or 'realtime' must be specified")

        if external_clock:
            step_sim_type = "external_clock"
            step_sim_value = "true"
        elif realtime:
            step_sim_type = "realtime"
            step_sim_value = 1
        elif timescale:
            if str(timescale).isdigit():
                step_sim_type = "timescale"
                step_sim_value = int(timescale)
            else:
                self.logger.info(f"timescale: {timescale} must be an integer value")
                raise JobException(f"timescale: {timescale} must be an integer value")

        return (step_sim_type, step_sim_value, start_datetime, end_datetime)

    def exec(self) -> None:
        self.init_sim()
        self.setup_points()
        self.advance_to_start_time()
        self.set_run_status(RunStatus.RUNNING)
        if self.step_sim_type == 'timescale' or self.step_sim_type == 'realtime':
            self.logger.info("Running timescale / realtime")
            self.run_timescale()
        elif self.step_sim_type == 'external_clock':
            self.logger.info("Running external_clock")
            self.start_message_loop()

    def init_sim(self):
        """Placeholder for all things necessary to initialize simulation"""

    def step(self):
        """Placeholder for making a step through simulation time

        Step should consist of the following:
            - Reading write arrays from mongo
            - check_sim_status_stop
            - if not self.stop
                - Update model inputs
                - Advancing the simulation
                - Check that advancing the simulation results in the correct expected timestep
                - Read output vals from simulation
                - Update Mongo with values
        """

    def advance_to_start_time(self):
        """Placeholder to advance sim to start time for job"""

    def update_model_inputs_from_write_arrays(self):
        """Placeholder for getting write values from Mongo and writing into simulation BEFORE a simulation timestep"""

    def write_outputs_to_mongo(self):
        """Placeholder for updating the current values exposed through Mongo AFTER a simulation timestep"""

    def update_sim_time_in_mongo(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""

    def create_tag_dictionaries(self):
        """Placeholder for method necessary to create Haystack entities and records"""

    def config_paths_for_model(self):
        """Placeholder for configuring necessary files for running model"""

    def run_external_clock(self):
        """Placeholder for running using an external_clock"""

    def run_timescale(self):
        if self.first_step_warmup:
            # Do first step outside of loop so warmup time is not counted against steps_behind
            self.advance()
        next_step_time = datetime.datetime.now() + self.timescale_step_interval()
        while self.is_running:

            if datetime.datetime.now() >= next_step_time:
                steps_behind = (datetime.datetime.now() - next_step_time) / self.timescale_step_interval()
                if steps_behind > 2.0:
                    raise JobExceptionSimulation("Timescale too high. Simulation more than 2 timesteps behind")
                next_step_time = next_step_time + self.timescale_step_interval()
                self.advance()

            if self.check_simulation_stop_conditions():
                self.stop()

            self._check_messages()

    def timescale_step_interval(self):
        return (self.time_per_step() / self.step_sim_value)

    def time_per_step(self) -> datetime.timedelta:
        raise NotImplementedError

    def check_simulation_stop_conditions(self) -> bool:
        """Placeholder to determine whether a simulation should stop"""
        return False

    def setup_points(self):
        """Placeholder for setting up points for I/O"""

    def setup_connections(self):
        """Placeholder until all db/connections operations can be completely moved out of the job"""
        self.mongo_db_recs = self.run_manager.mongo_db.recs
        self.mongo_db_sims = self.run_manager.mongo_db.sims
        self.mongo_db_write_arrays = self.run_manager.mongo_db.writearrays

        # InfluxDB
        self.historian_enabled = os.environ.get('HISTORIAN_ENABLE', False) == 'true'
        if self.historian_enabled:
            self.influx_db_name = os.environ['INFLUXDB_DB']
            self.influx_client = InfluxDBClient(host=os.environ['INFLUXDB_HOST'],
                                                username=os.environ['INFLUXDB_ADMIN_USER'],
                                                password=os.environ['INFLUXDB_ADMIN_PASSWORD'])
        else:
            self.influx_db_name = None
            self.influx_client = None

    @message
    def advance(self) -> None:
        self.step()

    @message
    def stop(self) -> None:
        super().stop()
        self.set_run_status(RunStatus.STOPPING)

    def cleanup(self) -> None:
        super().cleanup()
        self.set_run_status(RunStatus.COMPLETE)
