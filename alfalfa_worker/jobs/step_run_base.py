import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import auto

from alfalfa_worker.lib.alfalfa_connections_manager import (
    AlafalfaConnectionsManager
)
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

    # Timeouts
    # These are mostly used for the StepRunProcess class to clean up the subprocess
    # when it hangs.

    # How long can an advance call run before something bad is assumed to have happened.
    advance_timeout: int = 45
    # How long can it take a simulation to start before something bad is assumed to have happened.
    start_timeout: int = 300
    # Same as previous timeouts, but related to stopping
    stop_timeout: int = 45

    # How many timesteps can a timescale run lag behind before being stopped
    timescale_lag_limit: int = 2

    def __init__(self, realtime: bool, timescale: int, external_clock: bool, start_datetime: str, end_datetime: str):
        self.logger = logging.getLogger(self.__class__.__name__)

        if external_clock:
            self.clock_source = ClockSource.EXTERNAL
        else:
            self.clock_source = ClockSource.INTERNAL

        self.logger.debug(f"Clock Source: {self.clock_source}")

        self.start_datetime = datetime.strptime(start_datetime, DATETIME_FORMAT)
        self.end_datetime = datetime.strptime(end_datetime, DATETIME_FORMAT)
        self.logger.debug(f"Start Datetime: {self.start_datetime}")
        self.logger.debug(f"End Datetime: {self.end_datetime}")

        if realtime:
            self.timescale = 1
        else:
            self.timescale = timescale

        if self.clock_source == ClockSource.INTERNAL:
            self.logger.debug(f"Timescale: {self.timescale}")

        # Check for at least one of the required parameters
        if not realtime and not timescale and not external_clock:
            raise JobException("At least one of 'external_clock', 'timescale', or 'realtime' must be specified")

    @property
    def advance_interval(self) -> timedelta:
        """Get the timedelta for how often a simulation should be advanced
        based on the timescale and timestep_duration
        """
        if self.timestep_duration and self.timescale:
            return self.timestep_duration / self.timescale
        return None

    @property
    def timesteps_per_hour(self) -> int:
        """Get advance step time in terms of how many steps are requried
        to advance the model one hour
        """
        return int(timedelta(hours=1) / self.timestep_duration)


class StepRunBase(Job):
    def __init__(self, run_id: str, realtime: bool, timescale: int, external_clock: bool, start_datetime: str, end_datetime: str) -> None:
        """Base class for all jobs to step a run. The init handles the basic configuration needed
        for the derived classes.

        Args:
            run_id (str): Run object ID.
            realtime (bool): Simulate the model in realtime.
            timescale (int): Timescale in seconds of the simulation.
            external_clock (bool): Use an external clock to step the simulation.
            start_datetime (str): Start datetime. #TODO: this should be typed datetime
            end_datetime (str): End datetime. #TODO: this should be typed datetime
        """
        super().__init__()
        self.set_run_status(RunStatus.STARTING)
        self.options: Options = Options(to_bool(realtime), int(timescale), to_bool(external_clock), start_datetime, end_datetime)

        self.warmup_cleared = not self.options.warmup_is_first_step

        connections_manager = AlafalfaConnectionsManager()
        self.influx_db_name = connections_manager.influx_db_name
        self.influx_client = connections_manager.influx_client
        self.historian_enabled = connections_manager.historian_enabled

    def exec(self) -> None:
        self.logger.info("Initializing simulation...")
        self.initialize_simulation()
        self.logger.info("Simulation initialized.")
        self.set_run_status(RunStatus.STARTED)

        self.logger.info("Advancing to start time...")
        self.advance_to_start_time()
        if not self.warmup_cleared and self.options.clock_source == ClockSource.INTERNAL:
            self.advance()
        self.logger.info("Advanced to start time.")

        self.set_run_status(RunStatus.RUNNING)
        if self.options.clock_source == ClockSource.INTERNAL:
            self.logger.info("Running Simulation with Internal Clock.")
            self.run_timescale()
        elif self.options.clock_source == ClockSource.EXTERNAL:
            self.logger.info("Running Simulations with External Clock.")
            self.start_message_loop()

    def initialize_simulation(self) -> None:
        """Placeholder for all things necessary to initialize simulation"""
        raise NotImplementedError

    def advance_to_start_time(self):
        while self.run.sim_time < self.options.start_datetime:
            self.advance()
            self.warmup_cleared = True

    def run_timescale(self):
        """Run simulation at timescale"""
        next_advance_time = datetime.now() + self.options.advance_interval
        self.logger.debug(f"Advance interval is: {self.options.advance_interval}")
        self.logger.debug(f"Next step time: {next_advance_time}")

        while self.is_running:
            if datetime.now() >= next_advance_time:
                steps_behind = (datetime.now() - next_advance_time) / self.options.advance_interval
                if steps_behind > self.options.timescale_lag_limit:
                    raise JobExceptionSimulation(f"Timescale too high. Simulation more than {self.options.timescale_lag_limit} timesteps behind")
                next_advance_time = next_advance_time + self.options.advance_interval

                self.logger.debug(f"Internal clock called advance at {self.run.sim_time}")
                self.logger.debug(f"Next advance time: {next_advance_time}")
                self.advance()

            if self.check_simulation_stop_conditions() or self.run.sim_time >= self.options.end_datetime:
                self.logger.debug(f"Stopping at time: {self.run.sim_time}")
                self.stop()
                break

            self._check_messages()
        self.logger.info("Internal clock simulation has exited.")

    def get_sim_time(self) -> datetime:
        """Placeholder for method which retrieves time in the simulation"""
        raise NotImplementedError

    def update_run_time(self) -> None:
        """Update the sim_time in the Run object to match the most up to date sim_time"""
        self.set_run_time(self.get_sim_time())

    def check_simulation_stop_conditions(self) -> bool:
        """Placeholder to determine whether a simulation should stop.
        This can be used to signal that the simulation has exited and the job can now continue
        to clean up."""
        return False

    @message
    def stop(self) -> None:
        self.logger.info("Stopping simulation.")
        super().stop()
        self.set_run_status(RunStatus.STOPPING)

    def cleanup(self) -> None:
        super().cleanup()
        self.set_run_status(RunStatus.COMPLETE)

    @message
    def advance(self) -> None:
        """Placeholder for method which advances the simulation one timestep"""
        raise NotImplementedError
