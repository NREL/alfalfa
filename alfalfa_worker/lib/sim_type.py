from enum import auto

from alfalfa_worker.lib.auto_name_enum import AutoName


class SimType(AutoName):
    OPENSTUDIO = auto()
    MODELICA = auto()
    OTHER = auto()
