import json
import os
from datetime import datetime, timedelta
from typing import Callable

import openstudio
from pyenergyplus.api import EnergyPlusAPI

from alfalfa_worker.jobs.openstudio.lib.openstudio_component import (
    OpenStudioComponent
)
from alfalfa_worker.jobs.openstudio.lib.openstudio_point import OpenStudioPoint
from alfalfa_worker.jobs.step_run_process import StepRunProcess
from alfalfa_worker.lib.job_exception import (
    JobException,
    JobExceptionExternalProcess
)


def callback_wrapper(func):
    def wrapped_func(self: "StepRun", state):
        try:
            return func(self, state)
        except Exception:
            self.report_exception()
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

        self.logger.info('Generating variables from Openstudio output')
        self.ep_points: list[OpenStudioPoint] = []
        for alfalfa_json in self.run.dir.glob('**/run/alfalfa.json'):
            self.ep_points += [OpenStudioPoint(**point) for point in json.load(alfalfa_json.open())]

        def add_additional_meter(fuel: str, units: str, converter: Callable[[float], float]):
            meter_component = OpenStudioComponent("Meter", {"meter_name": f"{fuel}:Building"}, converter)
            meter_point = OpenStudioPoint(id=f"whole_building_{fuel.lower()}", name=f"Whole Building {fuel}", units=units)
            meter_point.output = meter_component
            self.ep_points.append(meter_point)

        add_additional_meter("Electricity", "W", lambda x: x / self.options.timesteps_per_hour)
        add_additional_meter("NaturalGas", "W", lambda x: x / self.options.timesteps_per_hour)

        [point.attach_run(self.run) for point in self.ep_points]

        self.ep_api: EnergyPlusAPI = None
        self.ep_state = None

    def simulation_process_entrypoint(self):
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

        for point in self.ep_points:
            point.pre_initialize(self.ep_api, self.ep_state)

        return_code = self.ep_api.runtime.run_energyplus(state=self.ep_state, command_line_args=['-w', str(self.weather_file), '-d', str(self.dir / 'simulation'), '-r', str(self.idf_file)])
        self.logger.info(f"Exited simulation with code: {return_code}")
        if return_code != 0:
            self.check_for_errors()
            raise JobExceptionExternalProcess(f"EnergyPlus Exited with a non-zero exit code: {return_code}")

    def callback_message(self, message: bytes) -> None:
        """Callback for when energyplus records a messaage to the log"""
        try:
            self.logger.info(message.decode())
        except Exception:
            self.report_exception()

    def callback_error(self, state, message: bytes) -> None:
        """Callback for when energyplus records an error to the log.
        These 'Errors' include warnings and non-critical errors."""
        try:
            self.logger.error(message.decode())
        except Exception:
            self.report_exception()

    @callback_wrapper
    def initialize_handles(self, state):
        """Callback called at begin_new_environment. Enumerates Alfalfa points to connect
        them with handles that can be used to transact data with energyplus."""
        exceptions = []

        for point in self.ep_points:
            try:
                point.initialize(self.ep_api, state)
            except JobException as e:
                exceptions.append(e)

        if len(exceptions) > 0:
            ExceptionGroup("Exceptions generated while initializing EP handles", exceptions)
        self.run.save()

    @callback_wrapper
    def ep_begin_timestep(self, state):
        """Callback called at end_zone_timestep_after_zone_reporting. This is responsible for
        controlling simulation advancement, as well as """

        # If simulation is not 'Running' yet and energyplus is still warming up, short circuit method and return
        if not self.running_event.is_set():
            warmup = self.ep_api.exchange.warmup_flag(state)
            kind_of_sim = self.ep_api.exchange.kind_of_sim(state)
            if warmup or kind_of_sim == 1:
                return

            # If execution makes it here it means the simulation has left warmup and needs to be readied for regular running
            self.update_run_time()
            self.running_event.set()

        # Update outputs from simulation
        self.ep_read_outputs()
        self.update_run_time()

        # Wait for event from main process
        self.advance_event.clear()
        while not self.advance_event.is_set() and not self.stop_event.is_set():
            self.advance_event.wait(1)

        # Handle stop event
        if self.stop_event.is_set():
            self.logger.info("Stop Event Set, stopping simulation")
            self.ep_api.runtime.stop_simulation(state)

        # Write inputs to energyplus
        self.ep_write_inputs()

    def get_sim_time(self) -> datetime:
        sim_time = self.options.start_datetime.replace(hour=0, minute=0) + timedelta(hours=self.ep_api.exchange.current_sim_time(self.ep_state))
        sim_time -= timedelta(minutes=1)  # Energyplus gives time at the end of current timestep, we want the beginning
        return sim_time

    def ep_read_outputs(self):
        """Reads outputs from E+ state"""
        influx_points = []
        for point in self.ep_points:
            value = point.update_output(self.ep_api, self.ep_state)
            if self.options.historian_enabled and value is not None:
                influx_points.append({"fields":
                                      {
                                          "value": value
                                      }, "tags":
                                      {
                                          "id": point.point.ref_id,
                                          "point": True,
                                          "source": "alfalfa"
                                      },
                                      "measurement": self.run.ref_id,
                                      "time": self.run.sim_time,
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
        for point in self.ep_points:
            point.update_input(self.ep_api, self.ep_state)

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

    def report_exception(self) -> None:
        super().report_exception(self.read_error_logs())
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
