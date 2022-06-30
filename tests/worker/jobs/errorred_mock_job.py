from tests.worker.lib.mock_job import MockJob


class ErrorredMockJob(MockJob):

    def exec(self):
        raise Exception
