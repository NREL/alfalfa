from alfalfa_worker.lib.job import JobExceptionMessageHandler, message
from tests.worker.lib.mock_job import MockJob


class MessageMockJob(MockJob):

    def __init__(self):
        super().__init__()
        self.create_empty_run()

    def exec(self) -> None:
        self.start_message_loop(20)

    @message
    def error(self):
        raise JobExceptionMessageHandler('ERROR')

    @message
    def repeat(self, payload):
        return payload
