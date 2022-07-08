from alfalfa_worker.lib.job import message
from tests.worker.lib.mock_job import MockJob


class LogReaderJob(MockJob):
    def __init__(self, run_id):
        super().__init__()
        self.checkout_run(run_id)

    @message
    def read_job_log(self):
        job_log_file = self.dir / 'jobs.log'
        return job_log_file.read_text()
