

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import JobStatus
from tests.worker.jobs.basic_mock_job import BasicMockJob
from tests.worker.jobs.errorred_mock_job import ErrorredMockJob
from tests.worker.utilities import wait_for_job_status


def test_mock_job_workflow(dispatcher: Dispatcher):
    params = {'foo': 1, 'bar': 2}
    test_job = dispatcher.create_job(BasicMockJob.job_path(), params)
    wait_for_job_status(test_job, JobStatus.INITIALIZED)
    test_job.start()
    wait_for_job_status(test_job, JobStatus.RUNNING, 10)
    wait_for_job_status(test_job, JobStatus.WAITING, 10)
    wait_for_job_status(test_job, JobStatus.STOPPED, 15)


def test_errorred_job_workflow(dispatcher: Dispatcher):
    errorred_job = dispatcher.create_job(ErrorredMockJob.job_path())
    errorred_job.start()
    wait_for_job_status(errorred_job, JobStatus.ERROR, 10)


def test_cannot_restart_stopped_job(dispatcher: Dispatcher):
    params = {'foo': 1, 'bar': 2}
    test_job = dispatcher.create_job(BasicMockJob.job_path(), params)
    wait_for_job_status(test_job, JobStatus.INITIALIZED)
    test_job.start()
    test_job.stop()
    wait_for_job_status(test_job, JobStatus.STOPPED)
    test_job.set_job_status(JobStatus.RUNNING)
    assert test_job.status is JobStatus.STOPPED
