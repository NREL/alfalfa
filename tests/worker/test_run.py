from uuid import uuid4

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import JobStatus
from alfalfa_worker.lib.run import RunStatus
from tests.worker.jobs.empty_job_1 import EmptyJob1
from tests.worker.jobs.empty_job_2 import EmptyJob2
from tests.worker.jobs.error_mock_job import ErrorMockJob
from tests.worker.jobs.file_io_mock_job import FileIOMockJob
from tests.worker.jobs.log_reader_job import LogReaderJob
from tests.worker.utilities import (
    send_message_and_wait,
    wait_for_job_status,
    wait_for_run_status
)


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


def test_checkin_on_run_error(dispatcher: Dispatcher):
    error_mock_job = dispatcher.create_job(ErrorMockJob.job_path())
    error_mock_job.start()

    run = error_mock_job.run

    # generate a random string to look for in the error log
    test_string = str(uuid4())

    send_message_and_wait(error_mock_job, 'throw_error_with_value', {'value': test_string})

    wait_for_run_status(run, RunStatus.ERROR)

    log_reader_job = dispatcher.create_job(LogReaderJob.job_path(), {'run_id': run.id})
    log_reader_job.start()

    response = send_message_and_wait(log_reader_job, 'read_job_log')
    log_contents = response['response']
    log_reader_job.stop()

    assert test_string in log_contents


def test_job_history(dispatcher: Dispatcher):
    # Create two runs with different jobs
    empty_job_1 = dispatcher.create_job(EmptyJob1.job_path())
    empty_job_2 = dispatcher.create_job(EmptyJob2.job_path())

    empty_job_1.start()
    empty_job_2.start()

    run_1 = empty_job_1.run
    run_2 = empty_job_2.run

    wait_for_job_status(empty_job_1, JobStatus.STOPPED)
    wait_for_job_status(empty_job_2, JobStatus.STOPPED)

    # Add second job to runs
    empty_job_1 = dispatcher.create_job(EmptyJob1.job_path(), {"run_id": run_2.id})
    empty_job_2 = dispatcher.create_job(EmptyJob2.job_path(), {"run_id": run_1.id})

    empty_job_1.start()
    empty_job_2.start()

    wait_for_job_status(empty_job_1, JobStatus.STOPPED)
    wait_for_job_status(empty_job_2, JobStatus.STOPPED)

    # make sure job_histories are correct
    assert run_1.job_history == [EmptyJob1.job_path(), EmptyJob2.job_path()]
    assert run_2.job_history == [EmptyJob2.job_path(), EmptyJob1.job_path()]
