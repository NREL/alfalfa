import datetime
import os

from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
from alfalfa_worker.lib.job import Job, JobException, message
from alfalfa_worker.lib.run import RunStatus


class StepRunBase(AlfalfaConnectionsBase, Job):
    def __init__(self, run_id, realtime, timescale, external_clock, start_datetime, end_datetime) -> None:
        super().__init__()
        self.checkout_run(run_id)
        self.set_run_status(RunStatus.STARTING)
        self.step_sim_type, self.step_sim_value, self.start_datetime, self.end_datetime = self.process_inputs(realtime, timescale, external_clock, start_datetime, end_datetime)
        self.logger.info(f"sim_type is {self.step_sim_type}")
        if self.step_sim_type == 'timescale':
            self.step_sim_value = self.step_sim_value
        elif self.step_sim_type == 'realtime':
            self.step_sim_value = 1
        else:
            self.step_sim_value = 5

        # Store the site for later use
        self.site = self.mongo_db_recs.find_one({"_id": self.run.id})

        self.start_datetime = datetime.datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
        self.end_datetime = datetime.datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S')

        self.historian_enabled = os.environ.get('HISTORIAN_ENABLE', False) == 'true'
        self.set_run_status(RunStatus.STARTED)

    def process_inputs(self, realtime, timescale, external_clock, start_datetime, end_datetime):
        # TODO change server side message: startDatetime to start_datetime
        timescale = False if timescale == 'undefined' else timescale

        # TODO remove after tests written
        self.logger.info(
            "start_datetime type: {}\tstart_datetime: {}".format(type(start_datetime), start_datetime))
        self.logger.info(
            "end_datetime type: {}\tend_datetime: {}".format(type(end_datetime), end_datetime))
        self.logger.info("realtime type: {}\trealtime: {}".format(type(realtime), realtime))
        self.logger.info("timescale type: {}\ttimescale: {}".format(type(timescale), timescale))
        self.logger.info(
            "external_clock type: {}\texternal_clock: {}".format(type(external_clock), external_clock))
        # Only want one of: realtime, timescale, or external_clock.  Else, reject configuration.
        # if (realtime and timescale) or (realtime and external_clock) or (timescale and external_clock):
        #    self.logger.info(
        #        "Only one of 'external_clock', 'timescale', or 'realtime' should be specified in message")
        #    sys.exit(1)

        # Check for at least one of the required parameters
        if not realtime and not timescale and not external_clock:
            # TODO: If exiting, what logging type to use?
            self.logger.info(
                "At least one of 'external_clock', 'timescale', or 'realtime' must be specified")
            raise JobException("At least one of 'external_clock', 'timescale', or 'realtime' must be specified")

        if external_clock:
            step_sim_type = "external_clock"
            step_sim_value = "true"
        elif realtime:
            step_sim_type = "realtime"
            step_sim_value = 1
        elif timescale:
            if str(timescale).isdigit():
                step_sim_type = "timescale"
                step_sim_value = int(timescale)
            else:
                self.logger.info(f"timescale: {timescale} must be an integer value")
                raise JobException(f"timescale: {timescale} must be an integer value")

        return (step_sim_type, step_sim_value, start_datetime, end_datetime)

    def exec(self) -> None:
        self.set_run_status(RunStatus.RUNNING)
        self.init_sim()
        self.setup_points()
        if self.step_sim_type == 'timescale' or self.step_sim_type == 'realtime':
            self.logger.info("Running timescale / realtime")
            self.run_timescale()
        elif self.step_sim_type == 'external_clock':
            self.logger.info("Running external_clock")
            self.run_external_clock()

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

    def write_outputs_to_mongo(self):
        """Placeholder for updating the current values exposed through Mongo AFTER a simulation timestep"""

    def update_sim_time_in_mongo(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""

    def create_tag_dictionaries(self):
        """Placeholder for method necessary to create Haystack entities and records"""

    def config_paths_for_model(self):
        """Placeholder for configuring necessary files for running model"""

    def run_external_clock(self):
        """Placeholder for running using an external_clock"""

    def run_timescale(self):
        """Placeholder for running using  an internal clock and a timescale"""

    def setup_points(self):
        """Placeholder for setting up points for I/O"""

    @message
    def stop(self) -> None:
        super().stop()
        self.set_run_status(RunStatus.STOPPING)

    def cleanup(self) -> None:
        super().cleanup()
        self.set_run_status(RunStatus.COMPLETE)