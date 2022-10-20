import inspect
import re
from pathlib import Path
from uuid import uuid4

import pytest

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import Job, JobStatus
from tests.worker.jobs.error_mock_job import ErrorMockJob
from tests.worker.utilities import send_message_and_wait, wait_for_job_status


@pytest.fixture
def error_mock_job(dispatcher: Dispatcher):

    yield dispatcher.create_job(ErrorMockJob.job_path())


def check_traceback(error_log: str):
    # Search for a traceback
    trace_line_re = re.compile('File\\s"([^"]*)", line ([0-9]*)')
    results = trace_line_re.findall(error_log)
    assert len(results) >= 2
    error_job_path = Path(inspect.getfile(ErrorMockJob.__class__))
    base_job_path = Path(inspect.getfile(Job.__class__))
    error_job_in_traceback = False
    base_job_in_traceback = False
    for (path, line) in results:
        if error_job_path.samefile(path):
            error_job_in_traceback = True
        if base_job_path.samefile(path):
            base_job_in_traceback = True
    assert error_job_in_traceback, "Traceback missing ErrorMockJob"
    assert base_job_in_traceback, "Traceback missing Job"


def test_exception_reporting(error_mock_job: ErrorMockJob):
    error_mock_job.start()

    # generate a random string to look for in the error log
    test_string = str(uuid4())

    send_message_and_wait(error_mock_job, 'throw_error_with_value', {'value': test_string})

    wait_for_job_status(error_mock_job, JobStatus.ERROR)

    # Is the test string in the error
    error_log = error_mock_job.run.error_log
    assert test_string in error_log

    # Search for a traceback
    check_traceback(error_log)


def test_failed_validation_reporting(error_mock_job: ErrorMockJob):
    error_mock_job.start()

    wait_for_job_status(error_mock_job, JobStatus.WAITING)

    error_mock_job.stop()

    wait_for_job_status(error_mock_job, JobStatus.ERROR)

    error_log = error_mock_job.run.error_log

    assert "JobExceptionFailedValidation" in error_log

    check_traceback(error_log)
