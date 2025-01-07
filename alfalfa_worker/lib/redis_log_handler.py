from logging import Handler, LogRecord

from alfalfa_worker.lib.alfalfa_connections_manager import (
    AlafalfaConnectionsManager
)
from alfalfa_worker.lib.models import Run


class RedisLogHandler(Handler):
    def __init__(self, run: Run, level: int | str = 0) -> None:
        super().__init__(level)
        connections_manager = AlafalfaConnectionsManager()
        self.redis = connections_manager.redis
        self.run = run

    def emit(self, record: LogRecord) -> None:
        self.redis.rpush(f"run:{self.run.ref_id}:log", self.format(record))
