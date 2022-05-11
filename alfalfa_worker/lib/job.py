import logging
import os
import shutil
import tarfile
import threading
from enum import Enum
from glob import glob
from typing import List

from redis import Redis

# from alfalfa_jobs.run import Run
from alfalfa_worker.lib.point import Point
from alfalfa_worker.lib.run import Run, RunStatus
from alfalfa_worker.lib.run_manager import RunManager


def message(func):
    """Decorator for methods which are triggered by messages.
    Overriding a function that has a decorator in the base class (like 'stop') will need to be decorated again."""
    setattr(func, 'message_handler', True)
    return func


class JobMetaclass(type):

    # Wrap Subclass __init__
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
            self._message_handlers = {}
            self._status = JobStatus.INITIALIZING
            self._result_paths = []
            # Redis
            self.redis = Redis(host=os.environ['REDIS_HOST'])
            self.redis_pubsub = self.redis.pubsub()
            self.runs = []
            logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
            self.base_logger = logging.getLogger("job_base")

            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                if hasattr(attr, 'message_handler'):
                    self._message_handlers[attr_name] = attr
            if __old_init__:
                __old_init__(self, *args, **kwargs)
        cls_dicts['__init__'] = __new_init__
        klazz = super().__new__(cls, name, bases, cls_dicts)

        if len(bases) == 0:
            klazz.jobs = []
        if len(bases) > 0:
            Job.jobs.append(klazz)
        return klazz


class Job(metaclass=JobMetaclass):
    run_manager: RunManager
    working_dir: str

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
            self.base_logger.info("Job running")
            self.exec()
            self._message_loop()
            # self._set_status(JobStatus.CLEANING_UP)
            # self.cleanup()
            self._set_status(JobStatus.STOPPED)
            self.base_logger.info("Job stopped")
        except Exception as e:
            print(e)
            self._set_status(JobStatus.ERROR)
            self.base_logger.info("Error in Job")
            raise

    def exec(self) -> None:
        """Runs job
        called by start()"""

    @message
    def stop(self) -> None:
        """Stop job"""
        self.base_logger.info("stop called")
        self._set_status(JobStatus.STOPPING)

    def cleanup(self) -> None:
        """Clean up job
        called after stopping"""
        self.tar_working_dir()
        self.delete_working_dir()

    def add_results_path(self, path):
        if len(os.path.commonpath([self.working_dir, path])) == 0:
            path = os.path.join(self.working_dir, path)
        self._result_paths.append(path)

    def join(self, *args):
        return os.path.join(self.working_dir, *args)

    def tar_working_dir(self) -> str:
        """tars job working dir
        if results_paths has stuff just add those, if not tar whole directory"""
        dir_name = os.path.split(self.working_dir)[-1]
        tar_path = os.path.join(self.working_dir, '..', f'{dir_name}.tar')
        tar = tarfile.TarFile(tar_path, 'w')
        if len(self._result_paths) > 0:
            for path in self._result_paths:
                files = glob(path)
                for file in files:
                    tar.add(file, arcname=os.path.relpath(file, start=self.working_dir))
        else:
            tar.add(self.working_dir, arcname='.')
        tar.close()
        return tar_path

    def delete_working_dir(self):
        shutil.rmtree(self.working_dir)

    def status(self) -> "JobStatus":
        """Get job status
        gives general status of job workflow"""
        return self._status

    def _set_status(self, status: "JobStatus"):
        # A callback could be added here to tell the client what the status is
        self._status = status

    def _message_loop(self):
        self.base_logger.info("message loop starting")
        for run in self.runs:
            self.redis.hset(run.id, 'control', 'idle')
        while self._status.value < JobStatus.STOPPING.value:
            self._check_messages()
        self.base_logger.info("message loop over")

    def _check_messages(self):
        self._status = JobStatus.WAITING
        message = self.redis_pubsub.get_message()
        if message and message['data'].__class__ == bytes:
            self.base_logger.info(f"recieved message: {message}")
            data = message['data'].decode('utf-8')
            if data in self._message_handlers.keys():
                self._status = JobStatus.RUNNING
                self._message_handlers[data]()
                self._redis_idle()

    def _redis_idle(self):
        for run in self.runs:
            self.redis.publish(run.id, 'complete')
            self.redis.hset(run.id, 'control', 'idle')

    def checkout_run(self, run_id, path='.') -> Run:
        run = self.run_manager.checkout_run(run_id, self.join(path))
        run.job_history.append(self.job_path())
        self.run_manager.update_db(run)
        self.listen_to_run(run)
        return run

    def checkin_run(self, run) -> Run:
        return self.run_manager.checkin_run(run)

    def create_run(self, upload_id: str, model_name: str, path='.') -> Run:
        run = self.run_manager.create_run_from_model(upload_id, model_name, self.join(path))
        self.listen_to_run(run)
        run.job_history.append(self.job_path())
        self.run_manager.update_db(run)
        return run

    @classmethod
    def job_path(cls):
        return f'{cls.__module__}.{cls.__name__}'

    def set_run_status(self, run: Run, status: RunStatus):
        run.status = status
        self.run_manager.update_db(run)

    def listen_to_run(self, run: Run):
        self.runs.append(run)
        self.redis_pubsub.subscribe(run.id)

    def add_points(self, run: Run, points: List[Point]):
        return self.run_manager.add_points(run, points)


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


class JobExceptionInvalidModel(BaseJobException):
    pass


class JobExceptionInvalidRun(BaseJobException):
    pass
