import json
import logging
import os
import threading
from enum import Enum
from json.decoder import JSONDecodeError

from redis import Redis

# from alfalfa_jobs.run import Run
from alfalfa_worker.lib.run import Run, RunStatus


def message(func):
    """Decorator for methods which are triggered by messages.
    Overriding a function that has a decorator in the base class (like 'stop') will need to be decorated again."""
    setattr(func, 'message_handler', True)
    return func


class JobMetaclass(type):
    """The purpose of the metaclass is to wrap the __init__ of the subclass.
    This allows the working_dir and run_manager arguments to be handled the same way
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
            self.working_dir = kwargs.get('working_dir')
            del kwargs['working_dir']
            self.run_manager = kwargs.get('run_manager')
            del kwargs['run_manager']
            self._status = JobStatus.INITIALIZING

            # Variables
            self.runs = []

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

    def start(self):
        if os.environ.get('THREADED_JOBS', '0') == '1':
            self.thread = threading.Thread(target=self._start)
            self.thread.start()
        else:
            self._start()

    def _start(self) -> None:
        """Job workflow"""
        try:
            self._set_status(JobStatus.STARTING)
            self._set_status(JobStatus.RUNNING)
            self.exec()
            self._message_loop()
            self._set_status(JobStatus.STOPPED)
        except Exception as e:
            print(e)
            self._set_status(JobStatus.ERROR)
            self.logger.info("Error in Job")
            raise

    def exec(self) -> None:
        """Runs job
        called by start()"""

    @message
    def stop(self) -> None:
        """Stop job"""
        self._set_status(JobStatus.STOPPING)

    def cleanup(self) -> None:
        """Clean up job
        called after stopping"""

    def join(self, *args):
        """Create a path relative to the job working directory
        like calling os.path.join(job.working_dir, *args)"""
        return os.path.join(self.working_dir, *args)

    def status(self) -> "JobStatus":
        """Get job status
        gives general status of job workflow"""
        return self._status

    def _set_status(self, status: "JobStatus"):
        if self._status is status:
            return
        self.logger.info(f"Job Status: {status.name}")
        # A callback could be added here to tell the client what the status is
        self._status = status

    def _message_loop(self):
        self.logger.info("message loop starting")
        for run in self.runs:
            self.redis.hset(run.id, 'control', 'idle')
        while self._status.value < JobStatus.STOPPING.value:
            self._check_messages()
        self.logger.info("message loop over")

    def _check_messages(self):
        self._set_status(JobStatus.WAITING)
        message = self.redis_pubsub.get_message()
        try:
            if message and message['data'].__class__ == bytes:
                self.logger.info(f"recieved message: {message}")
                data = json.loads(message['data'].decode('utf-8'))
                message_id = data.get('message_id')
                if data.get('method', None) in self._message_handlers.keys():
                    self._set_status(JobStatus.RUNNING)
                    response = {}
                    try:
                        response['response'] = self._message_handlers[data['method']](**data.get('params', {}))
                        response['status'] = "ok"
                    except JobExceptionMessageHandler as e:
                        # JobExceptionMessageHandler errors are thrown when the operation fails but the job isn't tainted.
                        # They are caught here so they don't cause the job to exit.
                        self.logger.error(e)
                        response['status'] = 'error'
                        response['response'] = str(e)
                    self.logger.info(f"message_id: {message_id}, response: {response}")
                    for run in self.runs:
                        self.redis.hset(run.id, message_id, json.dumps(response))
                        self.redis.hset(run.id, 'control', 'idle')
        except JSONDecodeError:
            self.logger.info("received malformed message")

    def checkout_run(self, run_id, path='.') -> Run:
        run = self.run_manager.checkout_run(run_id, self.join(path))
        run.job_history.append(self.job_path())
        self.run_manager.update_db(run)
        self.regster_run(run)
        return run

    def checkin_runs(self):
        for run in self.runs:
            self.checkin_run(run)

    def checkin_run(self, run) -> Run:
        return self.run_manager.checkin_run(run)

    def create_run(self, upload_id: str, model_name: str, path='.') -> Run:
        run = self.run_manager.create_run_from_model(upload_id, model_name, self.join(path))
        self.regster_run(run)
        run.job_history.append(self.job_path())
        self.run_manager.update_db(run)
        return run

    @classmethod
    def job_path(cls):
        return f'{cls.__module__}.{cls.__name__}'

    def set_run_status(self, run: Run, status: RunStatus):
        run.status = status
        self.run_manager.update_db(run)

    def regster_run(self, run: Run):
        self.runs.append(run)
        self.redis_pubsub.subscribe(run.id)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(run.join('jobs.log'))
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)


class JobStatus(Enum):
    """Enumeration of job states"""
    INITIALIZING = 0,
    STARTING = 2,
    RUNNING = 3,
    WAITING = 4,
    STOPPING = 8,
    CLEANING_UP = 9,
    STOPPED = 10,
    ERROR = 63


class BaseJobException(Exception):
    pass


class JobExceptionMessageHandler(BaseJobException):
    """Thrown when there is an execption that occurs in an message handler.
    This is caught and reported back to the caller via redis."""


class JobExceptionInvalidModel(BaseJobException):
    """Thrown when working on a model.
    ex: missing osw"""


class JobExceptionInvalidRun(BaseJobException):
    """Thrown when working on run.
    ex. run does not have necessary files"""
