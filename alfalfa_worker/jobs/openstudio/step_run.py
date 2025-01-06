import os
from datetime import datetime, timedelta
from typing import Callable

import openstudio
from pyenergyplus.api import EnergyPlusAPI

from alfalfa_worker.jobs.openstudio.lib.alfalfa_point import AlfalfaPoint
from alfalfa_worker.jobs.openstudio.lib.variables import Variables
from alfalfa_worker.jobs.step_run_process import StepRunProcess
from alfalfa_worker.lib.enums import PointType
from alfalfa_worker.lib.job import (
    JobException,
    JobExceptionExternalProcess,
    JobExceptionSimulation
)
from alfalfa_worker.lib.models import Point


def callback_wrapper(func):
    def wrapped_func(self: "StepRun", state):
        try:
            return func(self, state)
        except Exception:
            self.catch_exception()
    return wrapped_func


class StepRun(StepRunProcess):

    def __init__(self, run_id, realtime, timescale, external_clock, start_datetime, end_datetime) -> None:
        self.checkout_run(run_id)
        super().__init__(run_id, realtime, timescale, external_clock, start_datetime, end_datetime)
        self.options.timestep_duration = timedelta(minutes=1)

        # If idf_file is named "in.idf" we need to change the name because in.idf is not accepted by mlep
        # (likely mlep is using that name internally)
        # simulation/sim.idf is the assumed convention, but sim.idf may be a symlink
        original_idf_file = self.dir / 'simulation' / 'sim.idf'
        # Follow any symlink
        dst_idf_file = original_idf_file.resolve()
        self.idf_file = dst_idf_file.parents[0] / 'sim.idf'
        dst_idf_file.rename(self.idf_file)

        self.weather_file = os.path.realpath(self.dir / 'simulation' / 'sim.epw')

        self.variables = Variables(self.run)

        self.logger.info('Generating variables from Openstudio output')
        for alfalfa_json in self.run.dir.glob('**/run/alfalfa.json'):
            self.variables.generate_points(alfalfa_json)

        self.ep_api: EnergyPlusAPI = None
        self.ep_state = None

        self.additional_points: list[AlfalfaPoint] = []

    def start_simulation_process(self):
        """
        Initialize and start EnergyPlus co-simulation.

        :return:
        """
        self.prepare_idf()

        self.ep_api = EnergyPlusAPI()
        self.ep_state = self.ep_api.state_manager.new_state()
        self.ep_api.runtime.callback_begin_new_environment(self.ep_state,
                                                           self.initialize_handles)
        self.ep_api.runtime.callback_end_zone_timestep_after_zone_reporting(self.ep_state,
                                                                            self.ep_begin_timestep)
        self.ep_api.runtime.callback_message(self.ep_state, self.callback_message)
        self.ep_api.functional.callback_error(self.ep_state, self.callback_error)

        # Request output variables
        for point in self.variables.points.values():
            if "output" in point:
                if point["output"]["type"] == "OutputVariable":
                    self.ep_api.exchange.request_variable(self.ep_state, **point["output"]["parameters"])

        return_code = self.ep_api.runtime.run_energyplus(state=self.ep_state, command_line_args=['-w', str(self.weather_file), '-d', str(self.dir / 'simulation'), '-r', str(self.idf_file)])
        self.logger.info(f"Exited simulation with code: {return_code}")
        if return_code != 0:
            self.check_for_errors()
            raise JobExceptionExternalProcess(f"EnergyPlus Exited with a non-zero exit code: {return_code}")

    def callback_message(self, message: bytes) -> None:
        try:
            self.logger.info(message.decode())
        except Exception:
            self.catch_exception()

    def callback_error(self, state, message: bytes) -> None:
        try:
            self.logger.error(message.decode())
        except Exception:
            self.catch_exception()

    @callback_wrapper
    def initialize_handles(self, state):
        exceptions = []

        def get_handle(type, parameters):
            handle = None
            if type == "GlobalVariable":
                handle = self.ep_api.exchange.get_ems_global_handle(state, var_name=parameters["variable_name"])
            elif type == "OutputVariable":
                handle = self.ep_api.exchange.get_variable_handle(state, **parameters)
                self.logger.info(f"Got handle: {handle} for {parameters}")
            elif type == "Meter":
                handle = self.ep_api.exchange.get_meter_handle(state, **parameters)
            elif type == "Actuator":
                handle = self.ep_api.exchange.get_actuator_handle(state,
                                                                  component_type=parameters["component_type"],
                                                                  control_type=parameters["control_type"],
                                                                  actuator_key=parameters["component_name"])
            else:
                raise JobException(f"Unknown point type: {type}")
            if handle == -1:
                raise JobException(f"Handle not found for point of type: {type} and parameters: {parameters}")
            return handle

        def add_additional_meter(fuel: str, units: str, converter: Callable[[float], float]):
            try:
                handle = get_handle("Meter", {"meter_name": f"{fuel}:Building"})
                point = Point(ref_id=f"whole_building_{fuel.lower()}", name=f"Whole Building {fuel}", units=units, point_type=PointType.OUTPUT)
                self.run.add_point(point)
                alfalfa_point = AlfalfaPoint(point, handle, converter)
                self.additional_points.append(alfalfa_point)
            except JobException:
                return None

        add_additional_meter("Electricity", "W", lambda x: x / self.options.timesteps_per_hour)
        add_additional_meter("NaturalGas", "W", lambda x: x / self.options.timesteps_per_hour)

        for id, point in self.variables.points.items():
            try:
                if "input" in point:
                    handle = get_handle(point["input"]["type"], point["input"]["parameters"])
                    self.variables.points[id]["input"]["handle"] = handle
                if "output" in point:
                    if point["output"]["type"] == "Constant":
                        continue
                    self.variables.points[id]["output"]["handle"] = get_handle(point["output"]["type"], point["output"]["parameters"])
            except JobException as e:
                if point["optional"]:
                    self.logger.warn(f"Ignoring optional point '{point["name"]}'")
                    self.run.get_point_by_id(id).delete()
                else:
                    exceptions.append(e)
        if len(exceptions) > 0:
            ExceptionGroup("Exceptions generated while initializing EP handles", exceptions)
        self.run.save()

    @callback_wrapper
    def ep_begin_timestep(self, state):
        if not self.running_event.is_set():
            warmup = self.ep_api.exchange.warmup_flag(state)
            kind_of_sim = self.ep_api.exchange.kind_of_sim(state)
            if warmup or kind_of_sim == 1:
                return
            self.update_run_time()
            self.running_event.set()

        self.ep_read_outputs()
        self.update_run_time()

        self.advance_event.clear()
        while not self.advance_event.is_set() and not self.stop_event.is_set():
            self.advance_event.wait(1)

        if self.stop_event.is_set():
            self.logger.info("Stop Event Set, stopping simulation")
            self.ep_api.runtime.stop_simulation(state)
        self.ep_write_inputs()

    def get_sim_time(self) -> datetime:
        sim_time = self.options.start_datetime.replace(hour=0, minute=0) + timedelta(hours=self.ep_api.exchange.current_sim_time(self.ep_state))
        sim_time -= timedelta(minutes=1)  # Energyplus gives time at the end of current timestep, we want the beginning
        return sim_time

    def ep_read_outputs(self):
        """Reads outputs from E+ state"""
        influx_points = []
        for point in self.run.output_points:
            if point.ref_id not in self.variables.points:
                continue
            component = self.variables.points[point.ref_id]["output"]
            if "handle" not in component:
                continue
            handle = component["handle"]
            type = component["type"]
            value = None
            if type == "OutputVariable":
                value = self.ep_api.exchange.get_variable_value(self.ep_state, handle)
            elif type == "GlobalVariable":
                value = self.ep_api.exchange.get_ems_global_value(self.ep_state, handle)
            elif type == "Meter":
                value = self.ep_api.exchange.get_meter_value(self.ep_state, handle)
            elif type == "Actuator":
                value = self.ep_api.exchange.get_actuator_value(self.ep_state, handle)
            else:
                raise JobException(f"Invalid point type: {type}")
            if "multiplier" in component:
                self.logger.info(f"Applying a multiplier of '{component["multiplier"]}' to point '{point["name"]}'")
                value *= component["multiplier"]
            if self.ep_api.exchange.api_error_flag(self.ep_state):
                raise JobExceptionSimulation(f"EP returned an api error while reading from point: {point.name}")
            point.value = value
            if self.options.historian_enabled:
                influx_points.append({
                    "measurement": self.run.ref_id,
                    "time": self.run.sim_time,
                    "value": value,
                    "id": point.ref_id,
                    "point": True,
                    "source": "alfalfa"
                })
        for additional_point in self.additional_points:
            value = self.ep_api.exchange.get_meter_value(self.ep_state, additional_point.handle)
            value = additional_point.converter(value)
            additional_point.point.value = value
            if self.options.historian_enabled:
                influx_points.append({
                    "measurement": self.run.ref_id,
                    "time": self.run.sim_time,
                    "value": value,
                    "id": additional_point.point.ref_id,
                    "point": True,
                    "source": "alfalfa"
                })
        if self.historian_enabled:
            try:
                response = self.influx_client.write_points(points=influx_points,
                                                           time_precision='s',
                                                           database=self.influx_db_name)
            except ConnectionError as e:
                self.logger.error(f"Influx ConnectionError on curVal write: {e}")
            if not response:
                self.logger.warning(f"Unsuccessful write to influx.  Response: {response}")
                self.logger.info(f"Attempted to write: {influx_points}")
            else:
                self.logger.info(
                    f"Successful write to influx.  Length of JSON: {len(influx_points)}")

    def ep_write_inputs(self):
        """Writes inputs to E+ state"""
        for point in self.run.input_points:
            component = self.variables.points[point.ref_id]["input"]
            handle = component["handle"]
            type = component["type"]
            if type == "GlobalVariable" and point.value is not None:
                self.ep_api.exchange.set_ems_global_value(self.ep_state, handle, point.value)
            if type == "Actuator":
                if point.value is not None:
                    self.ep_api.exchange.set_actuator_value(self.ep_state, handle, point.value)
                    component["reset"] = False
                elif "reset" not in component or component["reset"] is False:
                    self.ep_api.exchange.reset_actuator(self.ep_state, handle)
                    component["reset"] = True

    def prepare_idf(self):
        """
        Replace the timestep and starting and ending year, month, day, day of week in the idf file.

        :return:
        """
        idf_path = openstudio.path(str(self.idf_file))
        workspace = openstudio.Workspace.load(idf_path)
        if not workspace.is_initialized():
            raise JobException("Cannot load idf file into workspace")
        workspace = workspace.get()

        delete_objects = [*workspace.getObjectsByType(openstudio.IddObjectType("RunPeriod")),
                          *workspace.getObjectsByType(openstudio.IddObjectType("Timestep"))]
        for object in delete_objects:
            workspace.removeObject(object.handle())

        runperiod_object = openstudio.IdfObject(openstudio.IddObjectType("RunPeriod"))
        runperiod_object.setString(0, "Alfalfa Run Period")
        runperiod_object.setInt(1, self.options.start_datetime.month)
        runperiod_object.setInt(2, self.options.start_datetime.day)
        runperiod_object.setInt(3, self.options.start_datetime.year)
        runperiod_object.setInt(4, self.options.end_datetime.month)
        runperiod_object.setInt(5, self.options.end_datetime.day)
        runperiod_object.setInt(6, self.options.end_datetime.year)
        runperiod_object.setString(7, str(self.options.start_datetime.strftime("%A")))

        timestep_object = openstudio.IdfObject(openstudio.IddObjectType("Timestep"))
        timestep_object.setInt(0, self.options.timesteps_per_hour)

        workspace.addObject(runperiod_object)
        workspace.addObject(timestep_object)

        paths_objects = workspace.getObjectsByType(openstudio.IddObjectType("PythonPlugin:SearchPaths"))
        python_paths = openstudio.IdfObject(openstudio.IddObjectType("PythonPlugin:SearchPaths"))
        python_paths.setString(0, "Alfalfa Virtual Environment Path")
        python_paths.setString(1, 'No')
        python_paths.setString(2, 'No')
        python_paths.setString(3, 'No')
        n = 4

        if (self.run.dir / '.venv').exists():
            python_paths.setString(n, str(self.run.dir / '.venv' / 'lib' / 'python3.12' / 'site-packages'))
            n += 1

        for path in paths_objects:
            for field_idx in range(4, path.numFields()):
                python_paths.setString(n, path.getString(field_idx).get())
                n += 1
            workspace.removeObject(path.handle())

        workspace.addObject(python_paths)

        workspace.save(idf_path, True)

    def catch_exception(self) -> None:
        super().catch_exception(self.read_error_logs())
        if self.ep_state is not None:
            self.ep_api.runtime.stop_simulation(self.ep_state)

    def read_error_logs(self) -> list[str]:
        error_logs = []
        for error_file in self.dir.glob('**/*.err'):
            error_log = f"{error_file}:\n"
            error_log += error_file.read_text()
            error_logs.append(error_log)
        return error_logs

    def check_for_errors(self):
        error_logs = self.read_error_logs()
        exception = JobExceptionExternalProcess("Energy plus terminated with error")
        for error_log in error_logs:
            exception.add_note(error_log)

        if "EnergyPlus Terminated" in '\n'.join(error_logs):
            raise exception
        super().check_for_errors()
