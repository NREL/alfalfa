from subprocess import check_call

from alfalfa_worker.lib.job import message
from tests.worker.lib.mock_job import MockJob


class SubprocessMockJob(MockJob):
    def __init__(self):
        super().__init__()
        self.create_empty_run()

    def exec(self) -> None:
        self.start_message_loop(120)

    @message
    def passing_subprocess(self):
        check_call("exit 0", shell=True)
        return True

    @message
    def failing_subprocess(self):
        check_call("exit 1", shell=True)
        return True

    @message
    def malformed_subprocess(self):
        # This will throw an error saying file not found as shell commands must be run with the Shell=True flag
        check_call("exit 0")
        return True
