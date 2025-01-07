from dataclasses import dataclass
from typing import Callable

from alfalfa_worker.lib.models import Point


@dataclass
class AlfalfaPoint:
    point: Point
    handle: int
    converter: Callable[[float], float] = lambda x: x
