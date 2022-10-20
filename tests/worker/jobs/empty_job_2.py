from tests.worker.lib.mock_job import MockJob


class EmptyJob2(MockJob):

    def __init__(self, run_id: str = None):
        super().__init__()
        if run_id:
            self.checkout_run(run_id)
        else:
            self.create_empty_run()

    def exec(self) -> None:
        pass
