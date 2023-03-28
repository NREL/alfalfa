from enum import Enum, auto


class AutoName(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name

    def __str__(self):
        return self.value

    @classmethod
    def possible_enums_as_string(cls):
        """Return the list of strings representing the enum values."""
        return [enum.value for enum in list(SimType)]


class SimType(AutoName):
    OPENSTUDIO = auto()
    MODELICA = auto()
    OTHER = auto()


class PointType(AutoName):
    INPUT = auto()
    OUTPUT = auto()
    BIDIRECTIONAL = auto()

    def __str__(self):
        return self.value


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
