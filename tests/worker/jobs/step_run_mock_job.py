import datetime
from datetime import timedelta
from time import sleep

from alfalfa_worker.jobs.step_run_base import StepRunBase
from alfalfa_worker.lib.job import message
from tests.worker.lib.mock_job import MockJob


class StepRunMockJob(MockJob, StepRunBase):

    def __init__(self, run_id, realtime, timescale, external_clock, start_datetime, end_datetime):
        super().__init__()
        self.checkout_run(run_id)
        StepRunBase.__init__(self, run_id, realtime, timescale, external_clock, start_datetime, end_datetime, skip_site_init=True)
        self.first_step_warmup = True
        self.simulation_step_duration = 1
        self.run.sim_time = self.start_datetime

    def step(self):
        sleep(self.simulation_step_duration)
        self.set_run_time(self.run.sim_time + self.time_per_step())

    def time_per_step(self) -> timedelta:
        return timedelta(seconds=60)

    def get_sim_time(self) -> datetime.datetime:
        return self.run.sim_time

    @message
    def set_simulation_step_duration(self, simulation_step_duration):
        self.simulation_step_duration = simulation_step_duration
