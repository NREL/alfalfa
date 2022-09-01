from enum import Enum, auto
from uuid import uuid4


class Point:
    """Input or Output point used to exchange data between simulation and client. TODO: can we extend this from the database object?"""

    def __init__(self, key: str, name: str, type, val=0, id=None, **kwargs) -> None:
        """
        Keyword arguments:
        key  -- The key that will be used by alfalfa job to find the variable in the simulation
        (this should be unique, but could be duplicated between input and output points if needed)
        name -- Human readable name
        type -- Is the point an Input or Output
        val  -- Initial value of the point (default: 0)
        id   -- unique ID in database (default: uuid4())
        kwargs -- Any other arguments that will be passed to the database object, used to catch unused args too
        """
        self.key = key
        self.name = name
        self.type = type if type.__class__ == PointType else PointType(type)
        self._val = val
        self.id = id if id is not None else str(uuid4())
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
