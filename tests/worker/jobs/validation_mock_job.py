from alfalfa_worker.lib.job import message
from tests.worker.lib.mock_job import MockJob


class ValidationMockJob(MockJob):
    def __init__(self):
        super().__init__()
        self.create_empty_run()
        self.test_file = self.dir / 'test.txt'
        self.test_text = "This is a test"

    def exec(self) -> None:
        self.start_message_loop()

    @message
    def create_file(self):
        with open(self.test_file, 'w') as f:
            f.write(self.test_text)

    def validate(self) -> None:
        assert self.test_file.exists(), "test file was not created"
        assert self.test_file.read_text() == self.test_text, "text in test file does not match expected value"
