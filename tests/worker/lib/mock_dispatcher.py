import os
import threading
from pathlib import Path

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import Job


class MockDispatcher(Dispatcher):

    def __init__(self, workdir: Path):
        os.chdir(workdir)
        super().__init__(workdir)

    def start_job(self, job_name, parameters) -> Job:
        os.chdir(self.workdir)
        job = self.create_job(job_name, parameters)
        thread = threading.Thread(target=job.start)
        thread.start()
        return job

    def add_model(self, model_path: os.PathLike):
        return self.run_manager.add_model(model_path)
