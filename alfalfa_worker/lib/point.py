from enum import Enum, auto
from uuid import uuid4


class Point:
    """Input or Ouput point used to exchange data between simulation and client"""

    def __init__(self, key: str, name: str, type, val=0, id=None) -> None:
        """
        Keyword arguments:
        key  -- The key that will be used by alfalfa job to find the variable in the simulation
        (this should be unique, but could be duplicated between input and output points if needed)
        name -- Human readable name
        type -- Is the point an Input or Output
        val  -- Initial value of the point (default: 0)
        id   -- unique ID in database (default: uuid4())"""
        self.key = key
        self.name = name
        self.type = type if type.__class__ == PointType else PointType(type)
        self._val = val
        if id is None:
            self.id = str(uuid4())
        else:
            self.id = id

        self._pending_value = False

    @property
    def val(self):
        return self._val

    @val.setter
    def val(self, new_val):
        if self.type == PointType.INPUT:
            raise AttributeError("Cannot write to an Input Point")
        self._val = new_val
        self._pending_value = True


class PointType(Enum):
    INPUT = auto()
    OUTPUT = auto()
    BIDIRECTIONAL = auto()

    def __str__(self):
        return self.value
