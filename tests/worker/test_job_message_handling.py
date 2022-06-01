from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import JobStatus
from tests.worker.jobs.message_mock_job import MessageMockJob
from tests.worker.utilities import send_message_and_wait, wait_for_job_status


def test_message_error_handling(dispatcher: Dispatcher):
    message_job = dispatcher.create_job(MessageMockJob.job_path())
    message_job.start()

    response = send_message_and_wait(message_job, 'error')
    assert response['status'] == 'error'
    message_job.stop()
    wait_for_job_status(message_job, JobStatus.STOPPED)


def test_message_response(dispatcher: Dispatcher):
    message_job = dispatcher.create_job(MessageMockJob.job_path())
    message_job.start()

    response = send_message_and_wait(message_job, 'repeat', {'payload': 'foo'})
    message_job.stop()
    assert response['status'] == 'ok'
    assert response['response'] == 'foo'


def test_message_stop(dispatcher: Dispatcher):
    message_job = dispatcher.create_job(MessageMockJob.job_path())
    message_job.start()

    response = send_message_and_wait(message_job, 'stop')
    assert response['status'] == 'ok'

    wait_for_job_status(message_job, JobStatus.STOPPED)
