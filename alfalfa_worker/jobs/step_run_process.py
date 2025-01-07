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

    def __init__(self, run_id: str, realtime: bool, timescale: int, external_clock: bool, start_datetime: str, end_datetime: str, **kwargs) -> None:
        super().__init__(run_id, realtime, timescale, external_clock, start_datetime, end_datetime)
        self.manager = Manager()
        self.advance_event = self.manager.Event()
        self.running_event = self.manager.Event()
        self.stop_event = self.manager.Event()
        self.error_event = self.manager.Event()
        self.error_log = self.manager.Value(c_wchar_p, '')
        self.simulation_process: Process
        self.subprocess: bool = False
        self.timestamp = self.manager.Value(c_wchar_p, '')

    def initialize_simulation(self) -> None:
        self.simulation_process = Process(target=StepRunProcess._start_simulation_process, args=(self,))
        self.simulation_process.start()

        self._wait_for_event(self.running_event, self.options.start_timeout, desired_event_set=True)
        self.update_run_time()

    def set_run_time(self, sim_time: datetime):
        if self.subprocess:
            self.timestamp.value = sim_time.strftime(DATETIME_FORMAT)
        else:
            return super().set_run_time(sim_time)

    def update_run_time(self) -> None:
        if self.subprocess:
            super().update_run_time()
        else:
            self.set_run_time(datetime.strptime(self.timestamp.value, DATETIME_FORMAT))

    def _start_simulation_process(self) -> None:
        self.subprocess = True
        try:
            return self.start_simulation_process()
        except Exception:
            self.catch_exception()

    def start_simulation_process(self) -> None:
        raise NotImplementedError

    def handle_process_error(self) -> None:
        if self.simulation_process.is_alive():
            self.simulation_process.kill()
        raise JobExceptionExternalProcess(self.error_log.value)

    def catch_exception(self, notes: list[str]) -> None:
        if self.subprocess:
            exception_log = exc_to_str()
            self.error_log.value = exception_log
            if len(notes) > 0:
                self.error_log.value += "\n\n" + '\n'.join(notes)
            self.error_event.set()

    def check_simulation_stop_conditions(self) -> bool:
        return not self.simulation_process.is_alive()

    def check_for_errors(self):
        exit_code = self.simulation_process.exitcode
        if exit_code:
            raise JobExceptionExternalProcess(f"Simulation process exited with non-zero exit code: {exit_code}")

    def _wait_for_event(self, event: threading.Event, timeout: float, desired_event_set: bool = False):
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
        self.logger.info("Stop called, stopping")
        if not self.stop_event.is_set():
            stop_start = time()
            self.stop_event.set()
            while (self.simulation_process.is_alive()
                   and time() - stop_start < self.options.stop_timeout
                   and not self.error_event.is_set()):
                pass
            if time() - stop_start > self.options.stop_timeout and self.simulation_process.is_alive():
                self.simulation_process.kill()
                raise JobExceptionExternalProcess("Simulation process stopped responding and was killed.")
            if self.error_event.is_set():
                self.handle_process_error()
