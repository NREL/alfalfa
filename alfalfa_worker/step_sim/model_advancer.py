# Standard library imports
import os
import time
from datetime import datetime

# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from alfalfa_worker.lib.alfalfa_connections import AlfalfaConnections
from alfalfa_worker.step_sim.model_logger import ModelLogger


class ModelAdvancer(object):
    """Base class for advancing models"""

    def __init__(self):
        # Parse args and extract to class variables

        # Having an arg parser here is a bit strange. Maybe just a partial to the argparser?
        from alfalfa_worker.step_sim.step_sim_utils import step_sim_arg_parser
        self.args = step_sim_arg_parser()
        self.site_id = self.args.site_id
        self.step_sim_type = self.args.step_sim_type
        if self.step_sim_type == 'timescale':
            self.step_sim_value = self.args.step_sim_value
        elif self.step_sim_type == 'realtime':
            self.step_sim_value = 1
        else:
            self.step_sim_value = None
        self.start_datetime = self.args.start_datetime  # datetime object
        self.end_datetime = self.args.end_datetime  # datetime object

        # Setup logging
        self.model_logger = ModelLogger()

        # Setup connections
        self.ac = AlfalfaConnections()
        self.site = self.ac.mongo_db_recs.find_one({"_id": self.site_id})

        # Setup tar file for downloading from s3
        self.parsed_path = '/parsed'
        self.sim_path = '/simulate'
        self.sim_path_site = os.path.join(self.sim_path, self.site_id)
        if not os.path.exists(self.sim_path_site):
            os.makedirs(self.sim_path_site)
        self.tar_name = "{}.tar.gz".format(self.site_id)
        self.tar_path = os.path.join(self.sim_path_site, self.tar_name)

        # Set state of simulation variables
        self.stop = False  # Stop == True used to end the simulation and initiate cleanup
        self.advance = False  # Advance == True condition specifically indicates a step shall be taken

    def set_db_status_running(self):
        """
        Set an idle state in Redis and update the simulation status in Mongo to Running.

        :return:
        """
        output_time_string = 's:{}'.format(self.start_datetime.strftime("%Y-%m-%d %H:%M"))
        self.ac.mongo_db_recs.update_one({"_id": self.site_id},
                                         {"$set": {"rec.datetime": output_time_string, "rec.simStatus": "s:Running"}})

    def check_sim_status_stop(self):
        """
        Check if the simulation status is either stopped or stopping

        :return:
        """
        status = self.site.get("rec", {}).get("simStatus")
        if status == "s:Stopped" or status == "s:Stopping":
            self.stop = True

    def run(self):
        """
        Main call to run.
        """
        self.set_idle_state()
        self.init_sim()
        self.set_db_status_running()
        if self.step_sim_type == 'timescale' or self.step_sim_type == 'realtime':
            self.run_timescale()
        elif self.step_sim_type == 'external_clock':
            self.run_external_clock()

    def set_idle_state(self):
        self.ac.redis.hset(self.site_id, 'control', 'idle')

    def check_stop_conditions(self):
        """Placeholder to check for all stopping conditions"""

    def init_sim(self):
        """Placeholder for all things necessary to initialize simulation"""

    def step(self):
        """Placeholder for making a step through simulation time

        Step should consist of the following:
            - Reading write arrays from mongo
            - check_sim_status_stop
            - if not self.stop
                - Update model inputs
                - Advancing the simulation
                - Check that advancing the simulation results in the correct expected timestep
                - Read output vals from simulation
                - Update Mongo with values
        """

    def update_model_inputs_from_write_arrays(self):
        """Placeholder for getting write values from Mongo and writing into simulation BEFORE a simulation timestep"""

    def update_db_with_model_outputs(self):
        """Placeholder for updating the current values exposed through Mongo AFTER a simulation timestep"""

    def update_sim_time_in_db(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""

    def create_tag_dictionaries(self):
        """Placeholder for method necessary to create Haystack entities and records"""

    def config_paths_for_model(self):
        """Placeholder for configuring necessary files for running model"""

    def cleanup(self):
        """Placeholder for cleaning up after simulation has completed"""

    def run_external_clock(self):
        """Placeholder for running using an external_clock"""

    def run_timescale(self):
        """Placeholder for running using  an internal clock and a timescale"""


if __name__ == '__main__':
    m = ModelAdvancer()
