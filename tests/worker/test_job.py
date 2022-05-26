
import json
import time
from typing import Dict
from uuid import uuid4

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import Job, JobStatus
from tests.worker.conftest import wait_for_status
from tests.worker.jobs.basic_mock_job import BasicMockJob
from tests.worker.jobs.errorred_mock_job import ErrorredMockJob
from tests.worker.jobs.message_mock_job import MessageMockJob
from tests.worker.jobs.subprocess_mock_job import SubprocessMockJob
from tests.worker.lib.mock_redis import MockRedis


def send_message(job: Job, method: str, params: Dict = {}):
    redis: MockRedis = job.redis
    run_id = job.run.id

    message_id = str(uuid4())
    message = {'method': method, 'message_id': message_id, 'params': params}
    redis.publish(run_id, json.dumps(message))
    return message_id


def send_message_and_wait(job: Job, method: str, params: Dict = {}, timeout=5):
    redis: MockRedis = job.redis
    run_id = job.run.id

    message_id = send_message(job, method, params)

    start_time = time.time()
    while timeout > time.time() - start_time:
        raw_response = redis.hget(run_id, message_id)
        if raw_response is None:
            continue
        return json.loads(raw_response)
    assert False, f"No response to message of method {method}"


def test_mock_job_workflow(dispatcher: Dispatcher):
    params = {'foo': 1, 'bar': 2}
    test_job = dispatcher.create_job(BasicMockJob.job_path(), params)
    wait_for_status(test_job, JobStatus.INITIALIZED)
    test_job.start()
    wait_for_status(test_job, JobStatus.RUNNING, 10)
    wait_for_status(test_job, JobStatus.WAITING, 10)
    wait_for_status(test_job, JobStatus.STOPPED, 15)


def test_errorred_job_workflow(dispatcher: Dispatcher):
    errorred_job = dispatcher.create_job(ErrorredMockJob.job_path())
    errorred_job.start()
    wait_for_status(errorred_job, JobStatus.ERROR, 10)


def test_message_error_handling(dispatcher: Dispatcher):
    message_job = dispatcher.create_job(MessageMockJob.job_path())
    message_job.start()

    response = send_message_and_wait(message_job, 'error')
    assert response['status'] == 'error'
    message_job.stop()
    wait_for_status(message_job, JobStatus.STOPPED)


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

    wait_for_status(message_job, JobStatus.STOPPED)


def test_subprocess_call(dispatcher: Dispatcher):
    subprocess_job = dispatcher.create_job(SubprocessMockJob.job_path())
    subprocess_job.start()

    wait_for_status(subprocess_job, JobStatus.WAITING)

    response = send_message_and_wait(subprocess_job, 'passing_subprocess')
    assert response['status'] == 'ok'
    assert response['response']

    wait_for_status(subprocess_job, JobStatus.WAITING)
    subprocess_job.stop()
    wait_for_status(subprocess_job, JobStatus.STOPPED)


def test_subprocess_call_error_1(dispatcher: Dispatcher):
    subprocess_job = dispatcher.create_job(SubprocessMockJob.job_path())
    subprocess_job.start()

    wait_for_status(subprocess_job, JobStatus.WAITING)

    response = send_message_and_wait(subprocess_job, 'failing_subprocess')
    assert response['response'] != 'True'
    assert response['status'] == 'error'

    wait_for_status(subprocess_job, JobStatus.ERROR)


def test_subprocess_call_error_2(dispatcher: Dispatcher):
    subprocess_job = dispatcher.create_job(SubprocessMockJob.job_path())
    subprocess_job.start()

    wait_for_status(subprocess_job, JobStatus.WAITING)

    response = send_message_and_wait(subprocess_job, 'malformed_subprocess')
    assert response['response'] != 'True'
    assert response['status'] == 'error'
    wait_for_status(subprocess_job, JobStatus.ERROR)


def test_cannot_restart_stopped_job(dispatcher: Dispatcher):
    params = {'foo': 1, 'bar': 2}
    test_job = dispatcher.create_job(BasicMockJob.job_path(), params)
    wait_for_status(test_job, JobStatus.INITIALIZED)
    test_job.start()
    test_job.stop()
    wait_for_status(test_job, JobStatus.STOPPED)
    test_job.set_job_status(JobStatus.RUNNING)
    assert test_job.status is JobStatus.STOPPED
