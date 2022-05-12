import glob
import os
from datetime import datetime
from enum import Enum, auto
from uuid import uuid4

import pytz
from dateutil import parser


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name


class RunStatus(AutoName):
    CREATED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    COMPLETE = auto()
    ERROR = auto()

    def __str__(self):
        return self.value


class Run:
    # A lot of stuff here is done to store in the db. It is messy. If we are sticking with mongo db or switching to something else it would be prettied.

    def __init__(self, dir, model, _id=str(uuid4()), job_history=[], status=RunStatus.CREATED, created=datetime.now(tz=pytz.UTC), modified=datetime.now(tz=pytz.UTC)):
        self.dir = dir
        self.model = model
        self.id = _id
        self._job_history = job_history
        self._status = status if status.__class__ == RunStatus else RunStatus(status)
        self.created = created if created.__class__ == datetime else parser.parse(created)
        self.modified = modified if modified.__class__ == datetime else parser.parse(modified)

    def join(self, *args):
        return os.path.join(self.dir, *args)

    def glob(self, search_str, recursive=True):
        return glob.glob(self.join(search_str), recursive=recursive)

    @property
    def job_history(self) -> list:
        return self._job_history

    @job_history.setter
    def job_history(self, value):
        self.modified = datetime.now(tz=pytz.UTC)
        self._job_history = value

    @property
    def status(self) -> RunStatus:
        return self._status

    @status.setter
    def status(self, value):
        self.modified = datetime.now(tz=pytz.UTC)
        self._status = value

    def to_dict(self):
        return {
            'model': self.model,
            '_id': self.id,
            'job_history': self._job_history,
            'status': str(self._status),
            'created': str(self.created),
            'modified': str(self.modified)
        }
