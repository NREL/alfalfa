from datetime import datetime, timedelta

from alfalfa_worker.jobs.step_run_base import StepRunBase
from alfalfa_worker.lib.enums import PointType
from alfalfa_worker.lib.job import message
from alfalfa_worker.lib.models import Point
from alfalfa_worker.lib.testcase import TestCase


class StepRun(StepRunBase):
    def __init__(self, run_id, realtime, timescale, external_clock, start_datetime: datetime, end_datetime) -> None:
        self.checkout_run(run_id)
        super().__init__(run_id, realtime, timescale, external_clock, start_datetime, end_datetime)

        self.logger.info(f"current datetime at start of simulation: {self.options.start_datetime}")

        # TODO: make configurable
        # step_size in seconds
        self.options.timestep_duration = timedelta(minutes=1)

        # run the FMU simulation
        self.set_run_time(self.options.start_datetime)

        # Allow model to warm up in first timestep without failing due to falling behind timescale
        self.options.warmup_is_first_step = True

    def initialize_simulation(self) -> None:
        fmupath = self.dir / 'model.fmu'
        # Load fmu
        config = {
            'fmupath': fmupath,
            'start_time': (self.options.start_datetime - datetime(self.options.start_datetime.year, 1, 1)) / timedelta(seconds=1),
            'step': self.options.timestep_duration / timedelta(seconds=1),
            'kpipath': self.dir / 'resources' / 'kpis.json'
        }
        # initiate the testcase -- NL make sure to flatten the config options to pass to kwargs correctly
        self.tc = TestCase(**config)

        self.setup_points()

    def check_simulation_stop_conditions(self) -> bool:
        return False

    def get_sim_time(self) -> datetime:
        sim_time = datetime(self.options.start_datetime.year, 1, 1, 0, 0, 0) + timedelta(seconds=float(self.tc.final_time))
        self.logger.info(f"Current Sim Time: {sim_time}")
        return sim_time

    def setup_points(self):
        fmu = self.tc.fmu
        self.variables = {}
        input_names: list[str] = fmu.get_model_variables(causality=2).keys()
        output_names = fmu.get_model_variables(causality=3).keys()

        def name_to_id(name: str) -> str:
            name.replace(" ", "_")
            return name

        for input in input_names:
            activate = input.endswith("_activate")
            name = input[0:-1 * (len("_activate"))] + "_u" if activate else input
            id = name_to_id(name)

            if id not in self.variables:
                self.variables[id] = {}

            if activate:
                self.variables[id]["activate"] = input
            else:
                point = Point(ref_id=id, name=name, point_type=PointType.INPUT)
                self.run.add_point(point)

        for output in output_names:
            point = Point(ref_id=name_to_id(output), name=output, point_type=PointType.OUTPUT)
            self.run.add_point(point)

        self.run.save()

    @message
    def advance(self):
        self.logger.info("advance called")
        # u represents simulation input values
        u = {}

        for point in self.run.input_points:
            value = point.value
            activate = "activate" in self.variables[point.ref_id]
            if value is not None:
                u[point.name] = value
                if activate:
                    u[point.name.replace('_u', '_activate')] = 1
            elif activate:
                u[point.name.replace('_u', '_activate')] = 0

        y_output = self.tc.advance(u)
        self.logger.debug(f"FMU output is {y_output}")
        self.update_run_time()

        # get each of the simulation output values and feed to the database
        influx_points = []
        for point in self.run.output_points:
            value = y_output[point.name]
            point.value = y_output

            if self.options.historian_enabled:
                influx_points.append({"fields":
                                      {
                                          "value": value,
                                      }, "tags":
                                      {
                                          "id": point.ref_id,
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
