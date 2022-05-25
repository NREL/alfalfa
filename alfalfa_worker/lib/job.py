import json
import logging
import os
import time
from enum import Enum
from json.decoder import JSONDecodeError
from typing import List
from xmlrpc.client import Boolean

from redis import Redis

from alfalfa_worker.lib.point import Point
from alfalfa_worker.lib.run import Run, RunStatus
from alfalfa_worker.lib.sim_type import SimType


def message(func):
    """Decorator for methods which are triggered by messages.
    Overriding a function that has a decorator in the base class (like 'stop') will need to be decorated again."""
    setattr(func, 'message_handler', True)
    return func


def with_run(func):
    """Decorator for methods which require a run.
    Will throw an error if called before a run is associated with the job."""

    def wrap(self, *args, **kwargs):
        if self.run is None:
            raise JobExceptionInvalidRun("Job has no associated run")
        return func(self, *args, **kwargs)
    return wrap


class JobMetaclass(type):
    """The purpose of the metaclass is to wrap the __init__ of the subclass.
    This allows the run_manager argument to be handled the same way
    in every job. These arguments are removed before calling the old __init__ function.
    This wrapper also does other setup functions like initializing redis and setting
    up message handlers for annotated functions."""
    # Wrap Subclass __init__. Called once for every class of Job
    def __new__(cls, name, bases, cls_dicts):
        if '__init__' in cls_dicts.keys():
            __old_init__ = cls_dicts['__init__']
        else:
            __old_init__ = None

        def __new_init__(self, *args, **kwargs):
            if hasattr(self, '_status') and self._status.value >= JobStatus.INITIALIZING.value:
                if __old_init__:
                    __old_init__(self, *args, **kwargs)
                return
            self.run_manager = kwargs.get('run_manager')
            del kwargs['run_manager']
            self._status = JobStatus.INITIALIZING

            # Variables
            self.run = None

            # Redis
            self.redis = Redis(host=os.environ['REDIS_HOST'])
            self.redis_pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
            logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
            self.logger = logging.getLogger(self.__class__.__name__)

            # Message Handlers
            self._message_handlers = {}
            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                if hasattr(attr, 'message_handler'):
                    self._message_handlers[attr_name] = attr
            if __old_init__:
                __old_init__(self, *args, **kwargs)
            self.set_job_status(JobStatus.INITIALIZED)
        cls_dicts['__init__'] = __new_init__
        klazz = super().__new__(cls, name, bases, cls_dicts)

        # This adds the job class to a list of all of the loaded jobs
        if len(bases) == 0:
            klazz.jobs = []
        if len(bases) > 0:
            Job.jobs.append(klazz)
        return klazz


class Job(metaclass=JobMetaclass):
    """Job Base Class"""

    def start(self) -> None:
        """Job workflow"""
        try:
            self.set_job_status(JobStatus.RUNNING)
            self.exec()
            if self.is_running:
                self.set_job_status(JobStatus.STOPPING)
                self.stop()
            self.set_job_status(JobStatus.CLEANING_UP)
            self.cleanup()
            self.set_job_status(JobStatus.STOPPED)

        except Exception as e:
            self.logger.error(e)
            self.set_job_status(JobStatus.ERROR)
            raise

    def exec(self) -> None:
        """Runs job
        called by start()
        If not overridden it will by default start the message loop."""
        self.start_message_loop()

    @message
    def stop(self) -> None:
        """Stop job"""

    def cleanup(self) -> None:
        """Clean up job
        called after stopping.
        If not overidden it will by default checkin the run"""
        if self.run is not None:
            self.checkin_run()

    def join(self, *args):
        """Create a path relative to the job working directory
        like calling os.path.join(self.run.dir, *args)"""
        return self.run.join(*args)

    @property
    def status(self) -> "JobStatus":
        """Get job status
        gives general status of job workflow"""
        return self._status

    @property
    def is_running(self) -> Boolean:
        return self._status.value < JobStatus.STOPPING.value

    def set_job_status(self, status: "JobStatus"):
        if self._status is status:
            return
        self.logger.info(f"Job Status: {status.name}")
        # A callback could be added here to tell the client what the status is
        self._status = status

    def start_message_loop(self, timeout=None):
        # Should the timeout be total time since loop started? or time since last message?
        start_time = time.time()
        while self.is_running and self.run is not None:
            if timeout is not None and time.time() - start_time > timeout:
                break
            self._check_messages()
        self.logger.info("message loop over")

    @with_run
    def _check_messages(self):
        self.set_job_status(JobStatus.WAITING)
        message = self.redis_pubsub.get_message()
        self.redis.hset(self.run.id, 'control', 'idle')
        # self.logger.info(message)
        try:
            if message and message['data'].__class__ == bytes:
                self.logger.info(f"recieved message: {message}")
                data = json.loads(message['data'].decode('utf-8'))
                message_id = data.get('message_id')
                method = data.get('method', None)
                if method == "stop":
                    self.set_job_status(JobStatus.STOPPING)
                if method in self._message_handlers.keys():
                    if self.is_running:
                        self.set_job_status(JobStatus.RUNNING)
                    response = {}
                    try:
                        response['response'] = self._message_handlers[data['method']](**data.get('params', {}))
                        response['status'] = 'ok'
                    except JobExceptionMessageHandler as e:
                        # JobExceptionMessageHandler errors are thrown when the operation fails but the job isn't tainted.
                        # They are caught here so they don't cause the job to exit.
                        self.logger.error(e)
                        response['status'] = 'error'
                        response['response'] = str(e)
                    self.logger.info(f"message_id: {message_id}, response: {response}")
                    self.redis.hset(self.run.id, message_id, json.dumps(response))
        except JSONDecodeError:
            self.logger.info("received malformed message")

    def checkout_run(self, run_id: str) -> Run:
        run = self.run_manager.checkout_run(run_id)
        run.job_history.append(self.job_path())
        self.run_manager.update_db(run)
        self.regster_run(run)
        return run

    @with_run
    def checkin_run(self):
        return self.run_manager.checkin_run(self.run)

    def create_run_from_model(self, upload_id: str, model_name: str, sim_type=SimType.OPENSTUDIO) -> None:
        run = self.run_manager.create_run_from_model(upload_id, model_name, sim_type)
        self.regster_run(run)
        run.job_history.append(self.job_path())
        self.run_manager.update_db(run)

    def create_empty_run(self):
        run = self.run_manager.create_empty_run()
        self.regster_run(run)

    @with_run
    def add_points(self, points: List[Point]):
        self.run_manager.add_points_to_run(self.run, points)

    @with_run
    def set_run_status(self, status: RunStatus):
        self.run.status = status
        self.run_manager.update_db(self.run)

    @with_run
    def set_run_time(self, sim_time):
        self.run.sim_time = sim_time
        self.run_manager.update_db(self.run)

    def regster_run(self, run: Run):
        self.run = run
        self.logger.info(run.dir)
        self.redis_pubsub.subscribe(run.id)
        self.redis.hset(self.run.id, 'control', 'idle')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(run.join('jobs.log'))
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    @classmethod
    def job_path(cls):
        return f'{cls.__module__}.{cls.__name__}'


class JobStatus(Enum):
    """Enumeration of job states"""
    INITIALIZING = 0
    INITIALIZED = 1
    RUNNING = 2
    WAITING = 4
    STOPPING = 8
    CLEANING_UP = 9
    STOPPED = 10
    ERROR = 63


class JobException(Exception):
    pass


class JobExceptionMessageHandler(JobException):
    """Thrown when there is an execption that occurs in an message handler.
    This is caught and reported back to the caller via redis."""


class JobExceptionInvalidModel(JobException):
    """Thrown when working on a model.
    ex: missing osw"""


class JobExceptionInvalidRun(JobException):
    """Thrown when working on run.
    ex. run does not have necessary files"""


class JobExceptionExternalProcess(JobException):
    """Thrown when an external process throws an error.
    ex. E+ can't run idf"""
