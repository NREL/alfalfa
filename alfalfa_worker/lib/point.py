from dataclasses import dataclass
from enum import Enum, auto
from uuid import uuid4


@dataclass
class Point:
    name: str
    type: "PointType"
    rec: dict
    id: str = uuid4()


class PointType(Enum):
    INPUT = auto(),
    OUTPUT = auto(),
    BIDIRECTIONAL = auto()
