
import subprocess

from alfalfa_worker.lib.job import Job


class FullRun(Job):

    def __init__(self, run_id) -> None:
        self.run = self.checkout_run(run_id)

    def exec(self) -> None:
        self.run_manager.set_run_status(self.run, 'Running')
        osws = self.run.glob("**/*.osw")
        for oswpath in osws:
            subprocess.call(['openstudio', 'run', "-w", oswpath])
        self.run_manager.complete_run(self.run)
