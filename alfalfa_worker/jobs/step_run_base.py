import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import auto

from influxdb import InfluxDBClient

from alfalfa_worker.lib.constants import DATETIME_FORMAT
from alfalfa_worker.lib.enums import AutoName, RunStatus
from alfalfa_worker.lib.job import Job, message
from alfalfa_worker.lib.job_exception import (
    JobException,
    JobExceptionSimulation
)
from alfalfa_worker.lib.utils import to_bool


class ClockSource(AutoName):
    INTERNAL = auto()
    EXTERNAL = auto()


@dataclass
class Options:
    clock_source: ClockSource

    start_datetime: datetime
    end_datetime: datetime

    # Ammount of time passed in the simulation during a single simulation step
    timestep_duration: timedelta

    # Timescale that an internal clock simulation will advance at
    timescale: int

    # Is the first step of the simulation responsible for running warmup
    warmup_is_first_step: bool = False

    # Should points be logged to InfluxDB
    historian_enabled: bool = os.environ.get('HISTORIAN_ENABLE', False) == 'true'

    advance_timeout: int = 45
    start_timeout: int = 300
    stop_timeout: int = 45
    # How many timesteps can a timescale run lag behind before being stopped
    timescale_lag_limit: int = 2

    def __init__(self, realtime: bool, timescale: int, external_clock: bool, start_datetime: str, end_datetime: str):
        print(f"external_clock: {external_clock}")
        if external_clock:
            self.clock_source = ClockSource.EXTERNAL
        else:
            print(f"setting source to: {ClockSource.INTERNAL}")
            self.clock_source = ClockSource.INTERNAL

        print(f"clock_source: {self.clock_source}")
        print(f"internal is: {ClockSource.INTERNAL}")

        self.start_datetime = datetime.strptime(start_datetime, DATETIME_FORMAT)
        self.end_datetime = datetime.strptime(end_datetime, DATETIME_FORMAT)

        if realtime:
            self.timescale = 1
        else:
            self.timescale = timescale

        # Check for at least one of the required parameters
        if not realtime and not timescale and not external_clock:
            raise JobException("At least one of 'external_clock', 'timescale', or 'realtime' must be specified")

    @property
    def advance_interval(self) -> timedelta:
        if self.timestep_duration and self.timescale:
            return self.timestep_duration / self.timescale
        return None

    @property
    def timesteps_per_hour(self) -> int:
        return int(timedelta(hours=1) / self.timestep_duration)


class StepRunBase(Job):
    def __init__(self, run_id: str, realtime: bool, timescale: int, external_clock: bool, start_datetime: str, end_datetime: str, **kwargs) -> None:
        """Base class for all jobs to step a run. The init handles the basic configuration needed
        for the derived classes.

        Args:
            run_id (str): Run object ID.
            realtime (bool): Simulate the model in realtime.
            timescale (int): Timescale in seconds of the simulation.
            external_clock (bool): Use an external clock to step the simulation.
            start_datetime (str): Start datetime. #TODO: this should be typed datetime
            end_datetime (str): End datetime. #TODO: this should be typed datetime
            **skip_site_init (bool): Skip the initialization of the site database object. This is mainly used in testing.
        """
        super().__init__()
        self.set_run_status(RunStatus.STARTING)
        self.options: Options = Options(to_bool(realtime), int(timescale), to_bool(external_clock), start_datetime, end_datetime)

        self.first_step_time: datetime = None
        self.next_step_time: datetime = None
        self.setup_connections()

    def exec(self) -> None:
        self.initialize_simulation()
        self.logger.info("Done initializing simulation")
        self.set_run_status(RunStatus.STARTED)
        self.advance_to_start_time()
        if self.options.warmup_is_first_step:
            self.advance()
        self.set_run_status(RunStatus.RUNNING)
        self.logger.info(f"Clock source: {self.options.clock_source}")
        if self.options.clock_source == ClockSource.INTERNAL:
            self.logger.info("Running Simulation with Internal Clock")
            self.run_timescale()
        elif self.options.clock_source == ClockSource.EXTERNAL:
            self.logger.info("Running Simulations with External Clock")
            self.start_message_loop()

    def initialize_simulation(self) -> None:
        """Placeholder for all things necessary to initialize simulation"""
        raise NotImplementedError

    def advance_to_start_time(self):
        self.logger.info("Advancing to start time")
        while self.run.sim_time < self.options.start_datetime:
            self.logger.info("Calling advance")
            self.advance()

    def create_tag_dictionaries(self):
        """Placeholder for method necessary to create Haystack entities and records"""

    def run_timescale(self):
        self.first_timestep_time = datetime.now()
        self.next_step_time = datetime.now() + self.options.advance_interval
        self.logger.info(f"Next step time: {self.next_step_time}")
        self.logger.info(f"Advance interval is: {self.options.advance_interval}")
        while self.is_running:
            if self.options.clock_source == ClockSource.INTERNAL:
                if datetime.now() >= self.next_step_time:
                    steps_behind = (datetime.now() - self.next_step_time) / self.options.advance_interval
                    if steps_behind > self.options.timescale_lag_limit:
                        raise JobExceptionSimulation(f"Timescale too high. Simulation more than {self.options.timescale_lag_limit} timesteps behind")
                    self.next_step_time = self.next_step_time + self.options.advance_interval
                    self.logger.info(f"Internal clock called advance at {self.run.sim_time}")
                    self.logger.info(f"Next step time: {self.next_step_time}")
                    self.advance()

                if self.check_simulation_stop_conditions() or self.run.sim_time >= self.options.end_datetime:
                    self.logger.info(f"Stopping at time: {self.run.sim_time}")
                    self.stop()
                    break

            self._check_messages()
        self.logger.info("Exitting timescale run")

    def get_sim_time(self) -> datetime:
        """Placeholder for method which retrieves time in the simulation"""
        raise NotImplementedError

    def update_run_time(self) -> None:
        self.set_run_time(self.get_sim_time())

    def check_simulation_stop_conditions(self) -> bool:
        """Placeholder to determine whether a simulation should stop"""
        return False

    def setup_connections(self):
        """Placeholder until all db/connections operations can be completely moved out of the job"""
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
    def stop(self) -> None:
        self.logger.info("Received stop command")
        super().stop()
        self.set_run_status(RunStatus.STOPPING)

    def cleanup(self) -> None:
        super().cleanup()
        self.set_run_status(RunStatus.COMPLETE)

    @message
    def advance(self) -> None:
        raise NotImplementedError
