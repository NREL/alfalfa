import glob
import os
from datetime import datetime
from enum import auto
from typing import List
from uuid import uuid4

import pytz
from dateutil import parser

from alfalfa_worker.lib.auto_name_enum import AutoName
from alfalfa_worker.lib.point import Point
from alfalfa_worker.lib.sim_type import SimType


class RunStatus(AutoName):
    CREATED = auto()
    PREPROCESSING = auto()
    READY = auto()
    STARTING = auto()
    STARTED = auto()
    RUNNING = auto()
    STOPPING = auto()
    COMPLETE = auto()
    ERROR = auto()


class Run:
    # A lot of stuff here is done to store in the db. It is messy. If we are sticking with mongo db or switching to something else it would be prettied.

    def __init__(self, dir=None, model=None, _id=None, job_history=[], sim_type=SimType.OPENSTUDIO, status=RunStatus.CREATED, created=None, modified=None, sim_time=None):
        self.dir = dir
        self.model = model
        self.id = _id if _id is not None else str(uuid4())
        self._job_history = job_history
        self._status = status if status.__class__ == RunStatus else RunStatus(status)
        self.sim_type = sim_type if sim_type.__class__ == SimType else SimType(sim_type)
        if created is None:
            created = datetime.now(tz=pytz.UTC)
        self.created = created if created.__class__ == datetime else parser.parse(created)
        if modified is None:
            modified = datetime.now(tz=pytz.UTC)
        self.modified = modified if modified.__class__ == datetime else parser.parse(modified)
        self.sim_time = sim_time
        self.points: List[Point] = []

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

    def get_point_by_key(self, key):
        for point in self.points:
            if key == point.key:
                return point
        return None

    def to_dict(self):
        return {
            'model': self.model,
            '_id': self.id,
            'job_history': self._job_history,
            'sim_type': str(self.sim_type),
            'status': str(self._status),
            'created': str(self.created),
            'modified': str(self.modified),
            'sim_time': str(self.sim_time)
        }


class RunException(Exception):
    pass
