import datetime
import os
from typing import Dict

import pytz
from influxdb import InfluxDBClient

from alfalfa_worker.lib.job import (
    Job,
    JobException,
    JobExceptionSimulation,
    message
)
from alfalfa_worker.lib.models import Rec, Simulation, Site
from alfalfa_worker.lib.run import RunStatus


class StepRunBase(Job):
    def __init__(self, run_id: str, realtime: bool, timescale: int, external_clock: bool, start_datetime: str, end_datetime: str, **kwargs) -> None:
        """Base class for all jobs to step a run. The init handles the basic configuration needed
        for the derived classes.

        Args:
            run_id (str): Run object ID.
            realtime (bool): Simulate the model in realtime.
            timescale (int): Timescale in seconds of the simulation.
            external_clock (bool): Use an external clock to step the simulation.
            start_datetime (str): Start datetime. #TODO: this should be typed datetime
            end_datetime (str): End datetime. #TODO: this should be typed datetime
            **skip_site_init (bool): Skip the initialization of the site database object. This is mainly used in testing.
            **skip_stop_db_writes (bool): Skip the writing of the stop results to the database. This is mainly used in testing.
        """
        super().__init__()
        self.set_run_status(RunStatus.STARTING)
        self.step_sim_type, self.step_sim_value, self.start_datetime, self.end_datetime = self.process_inputs(realtime, timescale, external_clock, start_datetime, end_datetime)
        self.logger.info(f"sim_type is {self.step_sim_type}")
        if self.step_sim_type == 'timescale':
            self.step_sim_value = self.step_sim_value
        elif self.step_sim_type == 'realtime':
            self.step_sim_value = 1
        else:
            self.step_sim_value = 5

        self.start_datetime = datetime.datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
        self.end_datetime = datetime.datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S')

        self.historian_enabled = os.environ.get('HISTORIAN_ENABLE', False) == 'true'

        self.first_step_warmup = False
        self.set_run_status(RunStatus.STARTED)

        self.setup_connections()
        if not kwargs.get('skip_site_init', False):
            # grab the new site from the new database model. This assumes that the site is the same as the old site
            try:
                # TODO: after passing around run ORM objects, convert to self.run.site
                self.site = Site.objects.get(ref_id=run_id)
            except Site.DoesNotExist:
                raise Exception(f"Could not find a site to step the run with run_id {run_id}")

        self.skip_stop_db_writes = kwargs.get('skip_stop_db_writes', False)

    def process_inputs(self, realtime, timescale, external_clock, start_datetime, end_datetime):
        # TODO change server side message: startDatetime to start_datetime
        timescale = False if timescale == 'undefined' else timescale

        # make sure the inputs are typed correctly
        try:
            timescale = int(timescale)
        except ValueError:
            self.logger.info(f"timescale is not an integer, continuing as sim_type=timescale. Value was {timescale}")

        if not isinstance(realtime, bool):
            realtime = True if realtime and realtime.lower() == 'true' else False
        if not isinstance(external_clock, bool):
            external_clock = True if external_clock and external_clock.lower() == 'true' else False

        self.logger.debug(f"start_datetime type: {type(start_datetime)}\tstart_datetime: {start_datetime}")
        self.logger.debug(f"end_datetime type: {type(end_datetime)}\tend_datetime: {end_datetime}")
        self.logger.debug(f"realtime type: {type(realtime)}\trealtime: {realtime}")
        self.logger.debug(f"timescale type: {type(timescale)}\ttimescale: {timescale}")
        self.logger.debug(f"external_clock type: {type(external_clock)}\texternal_clock: {external_clock}")

        # Check for at least one of the required parameters
        if not realtime and not timescale and not external_clock:
            self.logger.error("At least one of 'external_clock', 'timescale', or 'realtime' must be specified")
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
        self.init_sim()
        self.setup_points()
        self.advance_to_start_time()
        self.set_run_status(RunStatus.RUNNING)
        if self.step_sim_type == 'timescale' or self.step_sim_type == 'realtime':
            self.logger.info("Running timescale / realtime")
            self.run_timescale()
        elif self.step_sim_type == 'external_clock':
            self.logger.info("Running external_clock")
            self.start_message_loop()

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

    def advance_to_start_time(self):
        """Placeholder to advance sim to start time for job"""

    def update_model_inputs_from_write_arrays(self):
        """Placeholder for getting write values from Mongo and writing into simulation BEFORE a simulation timestep"""

    def write_outputs_to_redis(self):
        """Placeholder for updating the current values exposed through Redis AFTER a simulation timestep"""

    def update_sim_time_in_mongo(self):
        """Placeholder for updating the datetime in Mongo to current simulation time"""

    def create_tag_dictionaries(self):
        """Placeholder for method necessary to create Haystack entities and records"""

    def config_paths_for_model(self):
        """Placeholder for configuring necessary files for running model"""

    def run_external_clock(self):
        """Placeholder for running using an external_clock"""

    def run_timescale(self):
        if self.first_step_warmup:
            # Do first step outside of loop so warmup time is not counted against steps_behind
            self.advance()
        next_step_time = datetime.datetime.now() + self.timescale_step_interval()
        while self.is_running:
            if datetime.datetime.now() >= next_step_time:
                steps_behind = (datetime.datetime.now() - next_step_time) / self.timescale_step_interval()
                if steps_behind > 2.0:
                    raise JobExceptionSimulation("Timescale too high. Simulation more than 2 timesteps behind")
                next_step_time = next_step_time + self.timescale_step_interval()
                self.advance()

            if self.check_simulation_stop_conditions() or self.get_sim_time() >= self.end_datetime:
                self.stop()

            self._check_messages()

    def timescale_step_interval(self):
        return (self.time_per_step() / self.step_sim_value)

    def time_per_step(self) -> datetime.timedelta:
        raise NotImplementedError

    def get_sim_time(self) -> datetime.datetime:
        raise NotImplementedError

    def check_simulation_stop_conditions(self) -> bool:
        """Placeholder to determine whether a simulation should stop"""
        return False

    def setup_points(self):
        """Placeholder for setting up points for I/O"""

    def setup_connections(self):
        """Placeholder until all db/connections operations can be completely moved out of the job"""
        # InfluxDB
        self.historian_enabled = os.environ.get('HISTORIAN_ENABLE', False) == 'true'
        if self.historian_enabled:
            self.influx_db_name = os.environ['INFLUXDB_DB']
            self.influx_client = InfluxDBClient(host=os.environ['INFLUXDB_HOST'],
                                                username=os.environ['INFLUXDB_ADMIN_USER'],
                                                password=os.environ['INFLUXDB_ADMIN_PASSWORD'])
        else:
            self.influx_db_name = None
            self.influx_client = None

    @message
    def advance(self) -> None:
        self.step()

    @message
    def stop(self) -> None:
        super().stop()
        self.set_run_status(RunStatus.STOPPING)

        # Clear current values from the database when the simulation is no longer running
        if not self.skip_stop_db_writes:
            # grab the first rec object to unset some vars (this is the old site object).
            # I don't think that this is desired anymore.
            rec = Rec.objects.get(ref_id=self.run.ref_id)
            rec.update(rec__simStatus="s:Stopped", unset__rec__datetime=1, unset__rec__step=1)

            # get all the recs to disable the points (maybe this really needs to be on the Point objects?)
            for key in self.redis.scan_iter(f'site:{self.run.ref_id}:rec:*'):
                key = key.decode('UTF-8')
                self.redis.hset(key, mapping={'curStatus': 's:disabled'})
                self.redis.hdel(key, 'curVal', 'curErr')

            recs = self.site.recs(rec__writable="m:")
            recs.update(rec__writeStatus='s:disabled', unset__rec__writeLevel=1, unset__rec__writeVal=1, multi=True)

            # create the simulation database object. It appears that this is the only place
            # where this is created. Maybe we can remove this?
            time = str(datetime.datetime.now(tz=pytz.UTC))

            # If Modelica, then the testcase (tc) has some results. OpenStudio and
            # other inherited models do not expect this data.
            if hasattr(self, 'tc'):
                kpis = self.tc.get_kpis()
            else:
                kpis = None

            Simulation(
                name=self.site.name,
                site=self.site,
                time_completed=time,
                sim_status="Complete",
                s3_key=f"run/{self.run.ref_id}.tar.gz",
                results=kpis
            )

    def cleanup(self) -> None:
        super().cleanup()
        self.set_run_status(RunStatus.COMPLETE)

    def get_write_array_values(self) -> Dict[str, float]:
        """Return a dictionary of point ids and current winning values"""
        write_values = {}
        prefix = f'site:{self.site.ref_id}:point:'
        for key in self.redis.scan_iter(prefix + '*'):
            key = key.decode('UTF-8')
            _id = key[len(prefix):]
            write_array = self.redis.lrange(key, 0, -1)
            for value in write_array:
                if len(value) > 0:
                    write_values[_id] = float(value.decode('UTF-8'))
                    break

        return write_values
