import threading
from ctypes import c_wchar_p
from datetime import datetime
from multiprocessing import Manager, Process
from time import time

from alfalfa_worker.jobs.step_run_base import StepRunBase
from alfalfa_worker.lib.constants import DATETIME_FORMAT
from alfalfa_worker.lib.job import message
from alfalfa_worker.lib.job_exception import (
    JobExceptionExternalProcess,
    JobExceptionMessageHandler
)
from alfalfa_worker.lib.utils import exc_to_str


class StepRunProcess(StepRunBase):
    """Extension of StepRunBase with added functionality to handle cases where the simulation being run wants to be in control of the
    process instead of the other way round."""

    def __init__(self, run_id: str, realtime: bool, timescale: int, external_clock: bool, start_datetime: str, end_datetime: str, **kwargs) -> None:
        super().__init__(run_id, realtime, timescale, external_clock, start_datetime, end_datetime)

        # Create manager to handle communication between main process and simulation process
        self.manager = Manager()
        # advance_event: set by main process to signal simulation process to advance.
        # Cleared by simulation process immediately before waiting for a new advance event.
        self.advance_event = self.manager.Event()

        # stop_event: set by main process to signal simulation process to stop
        self.stop_event = self.manager.Event()

        # running_event: is set by simulation process when the simulation moves out of the warmup stage
        self.running_event = self.manager.Event()

        # error_event: set by simulation process to signal that an error has occurred
        self.error_event = self.manager.Event()
        # error_log: contains string serialized errors
        self.error_log = self.manager.Value(c_wchar_p, '')

        # timestamp: string serialized sim_time, set by simulation process after advancing
        self.timestamp = self.manager.Value(c_wchar_p, '')

        # simulation_process: object to contain simulation process
        self.simulation_process: Process

        # in_process: whether the current context is within simulation process or not
        self.in_subprocess = False

    def initialize_simulation(self) -> None:
        """Starts simulation process. Waits for running event to be set. And then records updated time."""
        self.simulation_process = Process(target=StepRunProcess._start_simulation_process, args=(self,))
        self.simulation_process.start()

        self._wait_for_event(self.running_event, self.options.start_timeout, desired_event_set=True)
        self.update_run_time()

    def set_run_time(self, sim_time: datetime) -> None:
        """In simulation process the sim_time is saved to the shared timestamp.
        In main process this calls the default implementation."""
        if self.in_subprocess:
            self.timestamp.value = sim_time.strftime(DATETIME_FORMAT)
        else:
            return super().set_run_time(sim_time)

    def update_run_time(self) -> None:
        """In simulation process calls default implementation.
        In main process sets run_time to the serialized timestamp from the simulation process."""
        if self.in_subprocess:
            super().update_run_time()
        else:
            self.set_run_time(datetime.strptime(self.timestamp.value, DATETIME_FORMAT))

    def _start_simulation_process(self) -> None:
        try:
            self.in_subprocess = True
            return self.simulation_process_entrypoint()
        except Exception:
            self.report_exception()

    def simulation_process_entrypoint(self) -> None:
        """Placeholder for spinning up the simulation"""
        raise NotImplementedError

    def handle_process_error(self) -> None:
        """This method is called in the main process when an error has been detected in the simulation process.
        It kills the simulation process if it is still alive and raises an exception with the contents of the process
        error log."""
        if self.simulation_process.is_alive():
            self.simulation_process.kill()
        raise JobExceptionExternalProcess(self.error_log.value)

    def report_exception(self, notes: list[str]) -> None:
        """This method should be called by the subclass, when an exception has occurred
        within the simulation process, to properly record the error log and signal that an error has occurred."""
        if self.in_subprocess:
            exception_log = exc_to_str()
            self.error_log.value = exception_log
            if len(notes) > 0:
                self.error_log.value += "\n\n" + '\n'.join(notes)
            self.error_event.set()

    def check_simulation_stop_conditions(self) -> bool:
        return not self.simulation_process.is_alive()

    def check_for_errors(self) -> None:
        """Checks for errors with the simulation_process and raises an exception if any are detected.
        This method should be overridden to add additional checks specific to a given process."""
        exit_code = self.simulation_process.exitcode
        if exit_code:
            raise JobExceptionExternalProcess(f"Simulation process exited with non-zero exit code: {exit_code}")

    def _wait_for_event(self, event: threading.Event, timeout: float, desired_event_set: bool = False) -> None:
        """Wait for a given event to go be set or cleared within a given amount of time"""
        wait_until = time() + timeout
        while (event.is_set() != desired_event_set
               and time() < wait_until
               and self.simulation_process.is_alive()
               and not self.error_event.is_set()):
            self.check_for_errors()
            if desired_event_set:
                event.wait(1)
        if self.error_event.is_set():
            self.handle_process_error()
        if not self.simulation_process.is_alive():
            self.check_for_errors()
            raise JobExceptionExternalProcess("Simulation process exited without returning an error")
        if time() > wait_until:
            self.simulation_process.kill()
            raise TimeoutError("Timedout waiting for simulation process to toggle event")

    @message
    def advance(self) -> None:
        self.logger.info(f"Advance called at {self.run.sim_time}")
        if self.advance_event.is_set():
            raise JobExceptionMessageHandler("Cannot advance, simulation is already advancing")
        self.advance_event.set()
        self._wait_for_event(self.advance_event, timeout=self.options.advance_timeout, desired_event_set=False)
        self.update_run_time()

    @message
    def stop(self):
        if not self.stop_event.is_set():
            stop_start_time = time()
            self.stop_event.set()
            while (self.simulation_process.is_alive()
                   and time() - stop_start_time < self.options.stop_timeout
                   and not self.error_event.is_set()):
                pass
            if time() - stop_start_time > self.options.stop_timeout and self.simulation_process.is_alive():
                self.simulation_process.kill()
                raise JobExceptionExternalProcess("Simulation process stopped responding and was killed.")
            if self.error_event.is_set():
                self.handle_process_error()
