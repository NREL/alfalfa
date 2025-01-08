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
        StepRunBase.__init__(self, run_id, realtime, timescale, external_clock, start_datetime, end_datetime, skip_site_init=True, skip_stop_db_writes=True)
        self.options.warmup_is_first_step = True
        self.options.timestep_duration = timedelta(minutes=1)
        self.run.sim_time = self.options.start_datetime

    def get_sim_time(self) -> datetime.datetime:
        return self.run.sim_time

    def initialize_simulation(self):
        pass

    @message
    def set_simulation_step_duration(self, simulation_step_duration):
        self.options.timestep_duration = timedelta(minutes=simulation_step_duration)

    @message
    def advance(self):
        sleep(self.options.timestep_duration)
        self.run.sim_time = self.run.sim_time + self.options.timestep_duration
