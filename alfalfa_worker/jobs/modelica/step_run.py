import json
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
        self.logger.info(f"{start_datetime}, {end_datetime}")
        sim_year = self.start_datetime.year
        self.sim_start_time = (self.start_datetime - datetime(sim_year, 1, 1)) / timedelta(seconds=1)
        self.sim_end_time = (self.end_datetime - datetime(sim_year, 1, 1)) / timedelta(seconds=1)

        self.logger.info(f"current datetime at start of simulation: {self.start_datetime}")

        fmupath = self.dir / 'model.fmu'
        tagpath = self.dir / 'tags.json'

        # TODO: make configurable
        # step_size in seconds
        self.step_size = 60

        # TODO cleanup
        self.realworld_timedelta = timedelta(seconds=float(self.step_size) / self.step_sim_value)
        print("real time per step: %", self.realworld_timedelta)

        # Load fmu
        config = {
            'fmupath': fmupath,
            'start_time': self.sim_start_time,
            'step': self.step_size,
            'kpipath': self.dir / 'resources' / 'kpis.json'
        }

        (self.tagid_and_outputs, self.id_and_dis, self.default_input) = self.create_tag_dictionaries(tagpath)

        # initiate the testcase -- NL make sure to flatten the config options to pass to kwargs correctly
        self.tc = TestCase(**config)

        # run the FMU simulation
        self.simtime = self.sim_start_time
        self.set_run_time(self.start_datetime)

        # Allow model to warm up in first timestep without failing due to falling behind timescale
        self.first_step_warmup = True

        if self.historian_enabled:
            self.logger.info("Historian enabled")

    def create_tag_dictionaries(self, tag_filepath):
        '''
        Purpose: matching the haystack display-name and IDs
        Inputs:  a json file containing all the tagged data
        Returns: a dictionary matching all outputs and IDs
                 a dictionary matching all IDs and display-names
                 a dictionary for every _enable input, set to value 0
        '''
        outputs_and_ID = {}
        id_and_dis = {}
        # default_input is a dictionary
        # with keys for every "_enable" input, set to value 0
        # in other words, disable everything
        default_input = {}

        # Get Haystack tag data, from tag_filepath
        tag_data = {}
        with open(tag_filepath) as json_data:
            tag_data = json.load(json_data)

        for point in tag_data:
            var_name = point['dis'].replace('s:', '')
            var_id = point['id'].replace('r:', '')

            id_and_dis[var_id] = var_name

            if 'writable' in point.keys():
                default_input[var_name.replace('_u', '_activate')] = 0

            if 'writable' not in point.keys() and 'point' in point.keys():
                outputs_and_ID[var_name] = var_id

        return (outputs_and_ID, id_and_dis, default_input)

    def check_simulation_stop_conditions(self) -> bool:
        return False

    def time_per_step(self):
        return timedelta(seconds=self.step_size)

    def update_sim_status(self):
        self.set_run_time(self.get_sim_time())

    def get_sim_time(self) -> datetime:
        return datetime(self.start_datetime.year, 1, 1, 0, 0, 0) + timedelta(seconds=float(self.tc.final_time))

    def step(self):
        # u represents simulation input values
        u = self.default_input.copy()
        # look in redis for current writearrays which has an array of controller
        # input values, the first element in the array with a value
        # is what should be applied to the simulation according to Project Haystack
        # convention. If there is no value in the array, then it will not be passed to the
        # simulation.
        for point in self.run.input_points:
            value = point.value
            if value is not None:
                u[point.name] = value
                u[point.name.replace('_u', '_activate')] = 1

        y_output = self.tc.advance(u)
        self.logger.debug(f"FMU output is {y_output}")
        self.update_sim_status()

        # get each of the simulation output values and feed to the database
        for point in self.run.output_points:
            point.value = y_output[point.name]

        if self.historian_enabled:
            self.write_outputs_to_influx(y_output)

    def write_outputs_to_influx(self, outputs):
        """
        Write output data to influx
        :return:
        """
        json_body = []
        base = {
            "measurement": self.run.ref_id,
            "time": "%s" % self.get_sim_time(),
        }
        response = False
        # get each of the simulation output values and feed to the database
        for key in outputs.keys():
            if key != 'time':
                output_id = self.tagid_and_outputs[key]
                value = outputs[key]
                dis = self.id_and_dis[output_id]
                base["fields"] = {
                    "value": value
                }
                base["tags"] = {
                    "id": output_id,
                    "dis": dis,
                    "siteRef": self.run.ref_id,
                    "point": True,
                    "source": 'alfalfa'
                }
                json_body.append(base.copy())
        try:
            print("Trying to write to influx")
            response = self.influx_client.write_points(points=json_body,
                                                       time_precision='s',
                                                       database=self.influx_db_name)
            if response:
                print("Influx response received %s" % response)
        except ConnectionError as e:
            print("Unable to write to influx: %s" % e)

    def setup_points(self):
        for id, dis in self.id_and_dis.items():
            point = Point(ref_id=id, name=dis)
            if dis in self.tagid_and_outputs.keys():
                point.point_type = PointType.OUTPUT
            else:
                point.point_type = PointType.INPUT
            self.run.add_point(point)

    @message
    def advance(self):
        self.logger.info("advance called")
        self.step()

    @message
    def stop(self):
        super().stop()
