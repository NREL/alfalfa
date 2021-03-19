# Standard library imports
from datetime import datetime, timedelta
import os
import pytz
import shutil
import sys
import tarfile
import uuid

from alfalfa_worker.lib.alfalfa_connections import AlfalfaConnections
from alfalfa_worker.step_sim.model_logger import ModelLogger


class ModelAdvancer(object):
    """Base class containing common setup code for simulation runs"""
    def __init__(self):
        # simulation step in seconds
        # TODO explicitly require that subclass of ModelAdvancer must set self.time_steps_per_hour before calling this init
        self.step_size = 3600.0 / self.time_steps_per_hour

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
        # Return a timedelta object to represent the real time between steps
        # This is used by the internal clock. Does not apply to the external clock
        self.step_realtimedelta = timedelta(seconds=(self.step_size / self.step_sim_value))
        self.set_start_end_datetimes()

        # Set up logging
        self.model_logger = ModelLogger()

        # Set up connections
        self.ac = AlfalfaConnections()
        self.site = self.ac.mongo_db_recs.find_one({"_id": self.site_id})

        # Set state of simulation variables
        self.stop = False  # Stop == True used to end the simulation and initiate cleanup
        self.advance = False  # Advance == True condition specifically indicates a step shall be taken

        # Global flag for using the historian
        self.historian_enabled = os.environ.get('HISTORIAN_ENABLE', False) == 'true'

    def run(self):
        """
        Main call to run.
        """
        self.set_idle_state()
        self.init_sim()
        self.set_db_status_running()
        self.ac.redis_pubsub.subscribe(self.site_id)
        if self.step_sim_type == 'timescale' or self.step_sim_type == 'realtime':
            self.model_logger.logger.info("Running timescale / realtime")
            self.run_timescale()
        elif self.step_sim_type == 'external_clock':
            self.model_logger.logger.info("Running external_clock")
            self.run_external_clock()


    def run_timescale(self):
        self.advance_to_start_time()

        realtime_next_step = datetime.now() + self.step_realtimedelta
        while True:

            if datetime.now() >= realtime_next_step:
                self.advance = True

            self.process_pubsub_message()

            if self.stop:
                self.cleanup()
                break

            if self.advance:
                self.step()
                self.update_db()
                self.set_redis_states_after_advance()
                # real world time to trigger next advance
                realtime_next_step = realtime_next_step + self.step_realtimedelta
                self.advance = False

    def set_db_status_running(self):
        """
        Update the simulation status in Mongo to Running.

        :return:
        """
        output_time_string = 's:{}'.format(self.start_datetime.strftime("%Y-%m-%d %H:%M"))
        self.ac.mongo_db_recs.update_one({"_id": self.site_id},
                                         {"$set": {"rec.datetime": output_time_string, "rec.simStatus": "s:Running"}})

    def check_sim_status_stop(self):
        """
        Check if the simulation status is either stopped or stopping
        and updates stop property
        TODO instead of setting self.stop, consider returning boolean

        :return:
        """
        status = self.site.get("rec", {}).get("simStatus")
        if status == "s:Stopped" or status == "s:Stopping":
            self.stop = True

    def set_idle_state(self):
        self.ac.redis.hset(self.site_id, 'control', 'idle')

    def check_stop_conditions(self):
        """Placeholder to check for all stopping conditions"""

    def init_sim(self):
        """Must be overwritten in subclasses."""
        pass

    def step(self):
        """Must be overwritten in subclasses.
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
        pass

    def update_model_inputs_from_write_arrays(self):
        """Must be overwritten in subclasses.
        Placeholder for getting write values from Mongo and writing into simulation BEFORE a simulation timestep
        """

    def write_outputs_to_mongo(self):
        """Placeholder for updating the current values exposed through Mongo AFTER a simulation timestep"""

    def update_sim_time_in_mongo(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""
        output_time_string = "s:" + self.current_sim_time()
        self.ac.mongo_db_recs.update_one({"_id": self.site_id}, {
            "$set": {"rec.datetime": output_time_string, "rec.step": "n:" + str(self.ep.kStep),
                     "rec.simStatus": "s:Running"}}, False)
    def current_sim_time(self):
        """Must be overwritten in subclasses.
        String representing current datetime of simulation.
        """
        pass
    def cleanup(self):
        """Must be overwritten in subclasses."""
        pass
    def advance_to_start_time(self):
        """Must be overwritten in subclasses."""
        pass
    def set_start_end_datetimes(self):
        """Set start_datetime and end_datetime, assuming input format %Y-%m-%d %H:%M:%S.  Override in subclass for alternate format."""
        self.start_datetime = datetime.strptime(self.args.start_datetime, '%Y-%m-%d %H:%M:%S')
        self.end_datetime = datetime.strptime(self.args.end_datetime, '%Y-%m-%d %H:%M:%S')



    def set_redis_states_after_advance(self):
        """Set an idle state in Redis"""
        self.ac.redis.publish(self.site_id, 'complete')
        self.ac.redis.hset(self.site_id, 'control', 'idle')

    def run_external_clock(self):
        self.advance_to_start_time()
        while True:
            self.process_pubsub_message()

            if self.stop:
                self.cleanup()
                break

            if self.advance:
                self.step()
                self.update_db()
                self.set_redis_states_after_advance()
                self.advance = False

    def process_pubsub_message(self):
        """
        Process message from pubsub and set relevant flags

        :return:
        """
        message = self.ac.redis_pubsub.get_message()
        if message:
            data = message['data']
            if data == b'advance':
                self.advance = True
            elif data == b'stop':
                self.stop = True

if __name__ == '__main__':
    m = ModelAdvancer()
