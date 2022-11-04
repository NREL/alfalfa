from uuid import uuid4

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import JobStatus
from tests.worker.jobs.subprocess_mock_job import SubprocessMockJob
from tests.worker.utilities import send_message_and_wait, wait_for_job_status


def test_subprocess_call(dispatcher: Dispatcher):
    subprocess_job = dispatcher.create_job(SubprocessMockJob.job_path())
    subprocess_job.start()

    wait_for_job_status(subprocess_job, JobStatus.WAITING)

    response = send_message_and_wait(subprocess_job, 'passing_subprocess')
    assert response['status'] == 'ok'
    assert response['response']

    wait_for_job_status(subprocess_job, JobStatus.WAITING)
    subprocess_job.stop()
    wait_for_job_status(subprocess_job, JobStatus.STOPPED)


def test_subprocess_call_error_1(dispatcher: Dispatcher):
    subprocess_job = dispatcher.create_job(SubprocessMockJob.job_path())
    subprocess_job.start()

    wait_for_job_status(subprocess_job, JobStatus.WAITING)

    response = send_message_and_wait(subprocess_job, 'failing_subprocess')
    assert response['response'] != 'True'
    assert response['status'] == 'error'

    wait_for_job_status(subprocess_job, JobStatus.ERROR)


def test_subprocess_call_error_2(dispatcher: Dispatcher):
    subprocess_job = dispatcher.create_job(SubprocessMockJob.job_path())
    subprocess_job.start()

    wait_for_job_status(subprocess_job, JobStatus.WAITING)

    response = send_message_and_wait(subprocess_job, 'malformed_subprocess')
    assert response['response'] != 'True'
    assert response['status'] == 'error'
    wait_for_job_status(subprocess_job, JobStatus.ERROR)


def test_subprocess_call_error_3(dispatcher: Dispatcher):
    subprocess_job = dispatcher.create_job(SubprocessMockJob.job_path())
    subprocess_job.start()

    wait_for_job_status(subprocess_job, JobStatus.WAITING)

    test_string = str(uuid4())

    response = send_message_and_wait(subprocess_job, 'failing_subprocess_with_output', {"test_string": test_string})
    assert response['response'] != 'True'
    assert response['status'] == 'error'

    wait_for_job_status(subprocess_job, JobStatus.ERROR)

    assert test_string in subprocess_job.run.error_log
