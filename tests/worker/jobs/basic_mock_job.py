from time import sleep

from tests.worker.lib.mock_job import MockJob


class BasicMockJob(MockJob):
    def __init__(self, foo, bar):
        super().__init__()
        self.foo = foo
        self.bar = bar
        self.create_empty_run()

    def exec(self):
        sleep(2)
        self.start_message_loop(10)
