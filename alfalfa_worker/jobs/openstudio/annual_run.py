
import subprocess

from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
from alfalfa_worker.lib.job import Job
from alfalfa_worker.lib.run import RunStatus


class AnnualRun(AlfalfaConnectionsBase, Job):

    def __init__(self, run_id) -> None:
        self.run = self.checkout_run(run_id)

    def exec(self) -> None:
        self.set_run_status(RunStatus.RUNNING)
        osws = self.run.glob("**/*.osw")
        for oswpath in osws:
            subprocess.check_call(['openstudio', 'run', "-w", oswpath])

        self.set_run_status(RunStatus.COMPLETE)
