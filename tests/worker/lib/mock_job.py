import threading

from alfalfa_worker.lib.job import Job
from tests.worker.lib.mock_redis import MockRedis


class MockJob(Job):

    def __init__(self):
        self.redis = MockRedis()
        self.redis_pubsub = self.redis.pubsub()

    def start(self) -> None:
        self.thread = threading.Thread(target=super().start)
        self.thread.start()
