import json
import logging
from datetime import datetime
from enum import Enum
from json.decoder import JSONDecodeError
from pathlib import Path
from subprocess import PIPE, Popen
from time import time

from alfalfa_worker.lib.alfalfa_connections_manager import (
    AlafalfaConnectionsManager
)
from alfalfa_worker.lib.enums import RunStatus, SimType
from alfalfa_worker.lib.job_exception import (
    JobExceptionExternalProcess,
    JobExceptionFailedValidation,
    JobExceptionInvalidRun,
    JobExceptionMessageHandler,
    JobExceptionTimeout
)
from alfalfa_worker.lib.models import Run
from alfalfa_worker.lib.redis_log_handler import RedisLogHandler
from alfalfa_worker.lib.utils import exc_to_str


def message(func):
    """Decorator for methods which are triggered by messages.
    Overriding a function that has a decorator in the base class (like 'stop') will need to be decorated again."""
    setattr(func, 'message_handler', True)
    return func


def with_run(return_on_fail=False):
    """Decorator for methods which require a run.
    Will throw an error if called before a run is associated with the job."""
    def inner(func):
        def wrap(self, *args, **kwargs):
            if self.run is None:
                if return_on_fail:
                    return
                raise JobExceptionInvalidRun("Job has no associated run")
            return func(self, *args, **kwargs)
        return wrap

    return inner


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

        def __new_init__(self: "Job", *args, **kwargs):
            if hasattr(self, '_status') and self._status.value >= JobStatus.INITIALIZING.value:
                if __old_init__:
                    __old_init__(self, *args, **kwargs)
                return
            self.run_manager = kwargs.get('run_manager')
            del kwargs['run_manager']
            self._status = JobStatus.INITIALIZING

            # Variables
            self.run = None

            connections_manager = AlafalfaConnectionsManager()

            # Redis
            self.redis = connections_manager.redis
            self.redis_pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
            self.logger = logging.getLogger(self.__class__.__name__)

            # Message Handlers
            self._message_handlers = {}
            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                if hasattr(attr, 'message_handler'):
                    self._message_handlers[attr_name] = attr
            if __old_init__:
                try:
                    __old_init__(self, *args, **kwargs)
                except Exception as e:
                    self.record_run_error(str(e))
                    raise e
            self.set_job_status(JobStatus.INITIALIZED)
        cls_dicts['__init__'] = __new_init__
        class_ = super().__new__(cls, name, bases, cls_dicts)

        # This adds the job class to a list of all of the loaded jobs
        if len(bases) == 0:
            class_.jobs = []
        if len(bases) > 0:
            Job.jobs.append(class_)
        return class_


def error_wrapper(func):
    def wrapped_func(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception:
            exc_str = exc_to_str()
            self.logger.error("Terminating Job with Error:")
            self.logger.error(exc_str)
            self.record_run_error(exc_str)
            self.set_job_status(JobStatus.ERROR)
            self.checkin_run()
    return wrapped_func


class Job(metaclass=JobMetaclass):
    """Job Base Class"""

    @error_wrapper
    def start(self) -> None:
        """Job workflow"""
        self.set_job_status(JobStatus.RUNNING)
        self.exec()
        if self.status == JobStatus.ERROR:
            return
        if self.is_running:
            self.set_job_status(JobStatus.STOPPING)
            self.stop()
        self.set_job_status(JobStatus.VALIDATING)
        try:
            self.validate()
        except AssertionError as e:
            raise JobExceptionFailedValidation(e)
        self.set_job_status(JobStatus.CLEANING_UP)
        self.cleanup()
        self.set_job_status(JobStatus.STOPPED)

    def exec(self) -> None:
        """Runs job
        called by start()
        If not overridden it will by default start the message loop."""
        self.start_message_loop()

    @message
    def stop(self) -> None:
        """Stop job"""
        self.set_job_status(JobStatus.STOPPING)

    def validate(self) -> None:
        """Placeholder method for validating a job completed successfully.
        It is recommended to validate using assert statements"""

    @with_run(return_on_fail=True)
    def cleanup(self) -> None:
        """Clean up job
        called after stopping.
        If not overridden it will by default checkin the run"""
        self.checkin_run()

    @property
    def status(self) -> "JobStatus":
        """Get job status
        gives general status of job workflow"""
        return self._status

    @property
    def is_running(self) -> bool:
        """Easily check if the state of the job is running or not"""
        return self._status.value < JobStatus.STOPPING.value

    @property
    @with_run(return_on_fail=True)
    def dir(self) -> Path:
        return self.run.dir

    def set_job_status(self, status: "JobStatus") -> None:
        if self._status is status:
            return
        # Once stopping we can't go back
        # this makes sure that the message loop will exit
        if not self.is_running and status.value < JobStatus.STOPPING.value:
            return
        self.logger.info(f"Job Status: {status.name}")
        # A callback could be added here to tell the client what the status is
        self._status = status
        if self.run:
            self.redis.hset(self.run.ref_id, 'job_status', status.name)

    def start_message_loop(self, timeout: float = None) -> None:
        # Should the timeout be total time since loop started? or time since last message?
        start_time = time()
        while self.is_running and self.run is not None:
            if timeout is not None and time() - start_time > timeout:
                break
            self.set_job_status(JobStatus.WAITING)
            self._check_messages()
        self.logger.info("message loop over")

    @with_run()
    def _check_messages(self) -> None:
        message = self.redis_pubsub.get_message()
        try:
            if message and message['data'].__class__ == bytes:
                self.logger.info(f"received message: {message}")
                data = json.loads(message['data'].decode('utf-8'))
                message_id = data.get('message_id')
                method = data.get('method', None)
                if method == "stop":
                    self.logger.info("Received stop message")
                    self.set_job_status(JobStatus.STOPPING)
                if method in self._message_handlers.keys():
                    if self.is_running:
                        self.set_job_status(JobStatus.RUNNING)
                    response = {}
                    try:
                        response['response'] = self._message_handlers[data['method']](**data.get('params', {}))
                        response['status'] = 'ok'
                    except JobExceptionMessageHandler:
                        # JobExceptionMessageHandler errors are thrown when the operation fails but the job isn't tainted.
                        # They are caught here so they don't cause the job to exit.
                        exc_str = exc_to_str()
                        self.logger.error(exc_str)
                        response['status'] = 'error'
                        response['response'] = exc_str
                    except Exception as e:
                        exc_str = exc_to_str()
                        response['status'] = 'error'
                        response['response'] = exc_str
                        raise e
                    finally:
                        self.redis.hset(self.run.ref_id, message_id, json.dumps(response))
                        self.logger.info(f"message_id: {message_id}, response: {response}")
        except JSONDecodeError:
            self.logger.info("received malformed message")

    def checkout_run(self, run_id: str) -> Run:
        run = self.run_manager.checkout_run(run_id)
        self.register_run(run)
        return run

    @with_run()
    def checkin_run(self) -> tuple[bool, str]:
        return self.run_manager.checkin_run(self.run)

    def create_run_from_model(self, model_id: str, sim_type=SimType.OPENSTUDIO, run_id=None) -> None:
        run = self.run_manager.create_run_from_model(model_id, sim_type, run_id=run_id)
        self.register_run(run)

    def create_empty_run(self) -> None:
        run = self.run_manager.create_empty_run()
        self.register_run(run)

    @with_run()
    def set_run_status(self, status: RunStatus) -> None:
        self.logger.info(f"Setting run status to {status.name}")
        self.run.status = status
        self.run.save()

    @with_run()
    def set_run_time(self, sim_time: datetime) -> None:
        self.run.sim_time = sim_time

    @with_run(return_on_fail=True)
    def record_run_error(self, error_log: str) -> None:
        self.set_run_status(RunStatus.ERROR)
        self.run.error_log = error_log
        self.run.save()

    def register_run(self, run: Run) -> None:
        self.run = run
        self.run.job_history.append(self.job_path())
        self.run.save()
        self.logger.debug(f"Attaching to run in directory: {run.dir}")

        self.redis_pubsub.subscribe(run.ref_id)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(self.dir / 'jobs.log')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        redis_handler = RedisLogHandler(self.run, logging.INFO)
        redis_handler.setFormatter(formatter)
        self.logger.addHandler(redis_handler)

    def log_subprocess(self, args: list[str], timeout: int = 300):
        self.logger.info(f"Executing process with args: '{args}'")

        process_log = []
        process = Popen(args, stdout=PIPE, stderr=PIPE, encoding='utf-8')
        wait_until = time() + timeout
        while (time() < wait_until and process.poll() is None):
            line = process.stdout.readline().rstrip()
            if len(line) > 0:
                process_log.append(line)
                self.logger.info(line)
            line = process.stderr.readline().rstrip()
            if len(line) > 0:
                process_log.append(line)
                self.logger.error(line)
        if time() > wait_until:
            process.kill()
            exception = JobExceptionTimeout(f"Process timedout after: {timeout} seconds")
            exception.add_note(process_log)
            raise exception
        exitcode = process.returncode
        if exitcode != 0:
            exception = JobExceptionExternalProcess(f"Process returned non-zero exit code: {exitcode}")
            exception.add_note('\n'.join(process_log))
            raise exception

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
    VALIDATING = 9
    CLEANING_UP = 10
    STOPPED = 11
    ERROR = 63
