from alfalfa_worker.lib.job import message
from tests.worker.lib.mock_job import MockJob


class ErrorMockJob(MockJob):

    def __init__(self):
        super().__init__()
        self.create_empty_run()

    def exec(self) -> None:
        self.start_message_loop()

    @message
    def throw_error_with_value(self, value: str):
        raise Exception(value)

    def validate(self) -> None:
        assert False
