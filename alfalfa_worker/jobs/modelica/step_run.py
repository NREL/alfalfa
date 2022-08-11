import json
from datetime import datetime, timedelta
from uuid import uuid4

import pytz

from alfalfa_worker.jobs.step_run_base import StepRunBase
from alfalfa_worker.lib.job import message
from alfalfa_worker.lib.testcase import TestCase


class StepRun(StepRunBase):
    def __init__(self, run_id, realtime, timescale, external_clock, start_datetime="0", end_datetime=str(60 * 60 * 24 * 365)) -> None:
        self.checkout_run(run_id)
        historian_year = 2017
        self.sim_start_time = float(start_datetime)
        self.sim_end_time = float(end_datetime)
        start_datetime = str(datetime(historian_year, 1, 1, 0, 0, 0) + timedelta(seconds=float(start_datetime)))
        end_datetime = str(datetime(historian_year, 1, 1, 0, 0, 0) + timedelta(seconds=float(end_datetime)))
        super().__init__(run_id, realtime, timescale, external_clock, start_datetime, end_datetime)
        self.logger.info(f"{start_datetime}, {end_datetime}")

        self.current_datetime = datetime(historian_year, 1, 1, 0, 0, 0) + timedelta(seconds=self.sim_start_time)
        print("current datetime at start of simulation: %", self.current_datetime)

        self.setup_connections()

        self.site = self.mongo_db_recs.find_one({"_id": self.run.id})

        fmupath = self.dir / 'model.fmu'
        tagpath = self.dir / 'tags.json'

        # TODO make configurable
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
        self.set_run_time(self.simtime)

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
        if self.simtime >= self.sim_end_time:
            return True
        return False

    def time_per_step(self):
        return timedelta(seconds=self.step_size)

    def update_sim_status(self):
        self.simtime = self.tc.final_time
        self.set_run_time(self.simtime)

    def step(self):
        # u represents simulation input values
        u = self.default_input.copy()
        # look in the database for current write arrays
        # for each write array there is an array of controller
        # input values, the first element in the array with a value
        # is what should be applied to the simulation according to Project Haystack
        # convention
        for array in self.mongo_db_write_arrays.find({"siteRef": self.run.id}):
            _id = array.get('_id')
            for val in array.get('val'):
                if val is not None:
                    dis = self.id_and_dis.get(_id)
                    if dis:
                        u[dis] = val
                        u[dis.replace('_u', '_activate')] = 1
                        break

        y_output = self.tc.advance(u)
        self.update_sim_status()
        self.increment_datetime()

        # get each of the simulation output values and feed to the database
        for key in y_output.keys():
            if key != 'time':
                output_id = self.tagid_and_outputs[key]
                value_y = y_output[key]
                self.mongo_db_recs.update_one({"_id": output_id}, {
                    "$set": {"rec.curVal": "n:%s" % value_y, "rec.curStatus": "s:ok", "rec.cur": "m:"}})

        if self.historian_enabled:
            self.write_outputs_to_influx(y_output)

    def increment_datetime(self):
        """
        The current datetime is incremented.
        :return:
        """
        self.current_datetime += timedelta(seconds=self.step_size)

    def write_outputs_to_influx(self, outputs):
        """
        Write output data to influx
        :return:
        """
        json_body = []
        base = {
            "measurement": self.run.id,
            "time": "%s" % self.current_datetime,
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
                    "siteRef": self.run.id,
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
        pass

    @message
    def advance(self):
        self.logger.info("advance called")
        self.step()

    @message
    def stop(self):
        super().stop()

        # DELETE
        # Clear all current values from the database when the simulation is no longer running
        self.mongo_db_recs.update_many({"site_ref": self.run.id, "rec.cur": "m:"},
                                       {"$unset": {"rec.curVal": "", "rec.curErr": ""},
                                           "$set": {"rec.curStatus": "s:disabled"}}, False)
        self.mongo_db_recs.update_many({"site_ref": self.run.id, "rec.writable": "m:"},
                                       {"$unset": {"rec.writeLevel": "", "rec.writeVal": ""},
                                           "$set": {"rec.writeStatus": "s:disabled"}}, False)

        time = str(datetime.now(tz=pytz.UTC))
        name = self.site.get("rec", {}).get("dis", "Test Case").replace('s:', '')
        kpis = json.dumps(self.tc.get_kpis())
        self.mongo_db_sims.insert_one(
            {"_id": str(uuid4()), "name": name, "siteRef": self.run.id, "simStatus": "Complete", "timeCompleted": time,
             "s3Key": f'run/{self.run.id}.tar.gz', "results": str(kpis)})
        # END DELETE
