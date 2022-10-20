from pathlib import Path

from alfalfa_worker.lib.job import JobExceptionMessageHandler, message
from tests.worker.lib.mock_job import MockJob


class FileIOMockJob(MockJob):

    def __init__(self, run_id: str = None):
        super().__init__()
        if run_id:
            self.checkout_run(run_id)
        else:
            self.create_empty_run()

    def exec(self) -> None:
        self.start_message_loop()

    @message
    def write(self, file_name: str, contents: str):
        with open(file_name, 'w') as f:
            f.write(contents)
        return True

    @message
    def read(self, file_name: str):
        file_path = Path(file_name)
        if not file_path.exists():
            raise JobExceptionMessageHandler("cannot read from file that does not exist")
        return file_path.read_text()
