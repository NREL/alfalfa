from enum import auto

from alfalfa_worker.lib.auto_name_enum import AutoName


class SimType(AutoName):
    OPENSTUDIO = auto()
    MODELICA = auto()
    OTHER = auto()

    @classmethod
    def possible_enums_as_string(cls):
        """Return the list of strings representing the enum values."""
        return [enum.value for enum in list(SimType)]
