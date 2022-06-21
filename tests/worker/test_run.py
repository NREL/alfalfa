from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import JobStatus
from tests.worker.jobs.file_io_mock_job import FileIOMockJob
from tests.worker.utilities import send_message_and_wait, wait_for_job_status


def test_run_file_conveyance(dispatcher: Dispatcher):
    file_io_job = dispatcher.create_job(FileIOMockJob.job_path())
    file_io_job.start()

    run_id = file_io_job.run.id

    wait_for_job_status(file_io_job, JobStatus.WAITING)

    test_file_name = 'test.txt'
    test_file_contents = 'this is a test'

    response = send_message_and_wait(file_io_job, 'write', {'file_name': test_file_name, 'contents': test_file_contents})
    assert response['status'] == 'ok'
    assert response['response']

    response = send_message_and_wait(file_io_job, 'read', {'file_name': test_file_name})
    assert response['status'] == 'ok'
    assert response['response'] == test_file_contents

    response = send_message_and_wait(file_io_job, 'read', {'file_name': 'non-existant-file.io'})
    assert response['status'] == 'error'

    wait_for_job_status(file_io_job, JobStatus.WAITING)

    file_io_job.stop()
    wait_for_job_status(file_io_job, JobStatus.STOPPED)

    file_io_job = dispatcher.create_job(FileIOMockJob.job_path(), {'run_id': run_id})
    file_io_job.start()

    response = send_message_and_wait(file_io_job, 'read', {'file_name': test_file_name})
    assert response['status'] == 'ok'
    assert response['response'] == test_file_contents

    file_io_job.stop()
    wait_for_job_status(file_io_job, JobStatus.STOPPED)
