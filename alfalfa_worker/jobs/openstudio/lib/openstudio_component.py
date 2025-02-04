
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from alfalfa_worker.lib.job_exception import JobException

# import pyenergyplus


class OpenStudioComponentType(Enum):
    ACTUATOR = "Actuator"
    CONSTANT = "Constant"
    OUTPUT_VARIABLE = "OutputVariable"
    GLOBAL_VARIABLE = "GlobalVariable"
    METER = "Meter"


@dataclass
class OpenStudioComponent:
    type: OpenStudioComponentType
    parameters: dict
    handle: int = None

    def __init__(self, type: str, parameters: dict, handle: int = None, converter: Callable[[float], float] = None):
        self.type = OpenStudioComponentType(type)
        self.parameters = parameters
        self.handle = handle

        if converter:
            self.converter = converter
        else:
            self.converter = lambda x: x

        if self.type == OpenStudioComponentType.ACTUATOR:
            self.reset = False

    def pre_initialize(self, api, state):
        if self.type == OpenStudioComponentType.OUTPUT_VARIABLE:
            api.exchange.request_variable(state, **self.parameters)

    def initialize(self, api, state):
        if self.type == OpenStudioComponentType.GLOBAL_VARIABLE:
            self.handle = api.exchange.get_ems_global_handle(state, var_name=self.parameters["variable_name"])
        elif self.type == OpenStudioComponentType.OUTPUT_VARIABLE:
            self.handle = api.exchange.get_variable_handle(state, **self.parameters)
        elif self.type == OpenStudioComponentType.METER:
            self.handle = api.exchange.get_meter_handle(state, **self.parameters)
        elif self.type == OpenStudioComponentType.ACTUATOR:
            self.handle = api.exchange.get_actuator_handle(state,
                                                           component_type=self.parameters["component_type"],
                                                           control_type=self.parameters["control_type"],
                                                           actuator_key=self.parameters["component_name"])
        elif self.type == OpenStudioComponentType.CONSTANT:
            return
        else:
            raise JobException(f"Unknown point type: {self.type}")

        if self.handle == -1:
            raise JobException(f"Handle not found for point of type: {self.type} and parameters: {self.parameters}")

    def read_value(self, api, state):
        if self.handle == -1 or self.handle is None:
            return None
        if self.type == OpenStudioComponentType.OUTPUT_VARIABLE:
            value = api.exchange.get_variable_value(state, self.handle)
        elif self.type == OpenStudioComponentType.GLOBAL_VARIABLE:
            value = api.exchange.get_ems_global_value(state, self.handle)
        elif self.type == OpenStudioComponentType.METER:
            value = api.exchange.get_meter_value(state, self.handle)
        elif self.type == OpenStudioComponentType.ACTUATOR:
            value = api.exchange.get_actuator_value(state, self.handle)
        elif self.type == OpenStudioComponentType.CONSTANT:
            value = self.parameters["value"]

        return self.converter(value)

    def write_value(self, api, state, value):
        if self.handle == -1 or self.handle is None:
            return None
        if self.type == OpenStudioComponentType.GLOBAL_VARIABLE and value is not None:
            api.exchange.set_ems_global_value(state, self.handle, value)
        if self.type == OpenStudioComponentType.ACTUATOR:
            if value is not None:
                api.exchange.set_actuator_value(state, self.handle, value)
                self.reset = False
            elif self.reset is False:
                api.exchange.reset_actuator(state, self.handle)
                self.reset = True
