from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import JobStatus
from alfalfa_worker.lib.run import RunStatus
from tests.worker.jobs.validation_mock_job import ValidationMockJob
from tests.worker.utilities import (
    send_message_and_wait,
    wait_for_job_status,
    wait_for_run_status
)


def test_passing_validation(dispatcher: Dispatcher):
    validation_job = dispatcher.create_job(ValidationMockJob.job_path())
    validation_job.start()

    wait_for_job_status(validation_job, JobStatus.WAITING)

    response = send_message_and_wait(validation_job, 'create_file')
    assert response['status'] == 'ok'

    wait_for_job_status(validation_job, JobStatus.WAITING)
    validation_job.stop()
    wait_for_job_status(validation_job, JobStatus.STOPPED)


def test_failing_validation(dispatcher: Dispatcher):
    validation_job = dispatcher.create_job(ValidationMockJob.job_path())
    validation_job.start()

    wait_for_job_status(validation_job, JobStatus.WAITING)

    validation_job.stop()
    wait_for_job_status(validation_job, JobStatus.ERROR)
    wait_for_run_status(validation_job.run, RunStatus.ERROR)
