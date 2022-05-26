

from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
from alfalfa_worker.lib.job import Job
from alfalfa_worker.lib.run import RunStatus
from alfalfa_worker.lib.testcase import TestCase


class AnnualRun(AlfalfaConnectionsBase, Job):

    def __init__(self, run_id) -> None:
        self.run = self.checkout_run(run_id)

    def exec(self) -> None:
        self.set_run_status(RunStatus.RUNNING)

        # Load fmu
        config = {
            'fmupath': self.run.join('model.fmu'),
            'step': 60
        }

        tc = TestCase(config)

        u = {}
        while tc.start_time < 10000:
            tc.advance(u)

        self.set_run_status(RunStatus.COMPLETE)
