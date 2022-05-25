
import json
from time import sleep
from uuid import uuid4

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import JobStatus
from tests.worker.conftest import wait_for_status
from tests.worker.jobs.basic_mock_job import BasicMockJob
from tests.worker.jobs.errorred_mock_job import ErrorredMockJob
from tests.worker.jobs.message_mock_job import MessageMockJob
from tests.worker.lib.mock_redis import MockRedis


def test_mock_job_workflow(dispatcher: Dispatcher):
    params = {'foo': 1, 'bar': 2}
    test_job = dispatcher.create_job(BasicMockJob.job_path(), params)
    assert wait_for_status(test_job, JobStatus.INITIALIZED)
    test_job.start()
    assert wait_for_status(test_job, JobStatus.RUNNING, 10)
    assert wait_for_status(test_job, JobStatus.WAITING, 10)
    assert wait_for_status(test_job, JobStatus.STOPPED, 15)


def test_errorred_job_workflow(dispatcher: Dispatcher):
    errorred_job = dispatcher.create_job(ErrorredMockJob.job_path())
    errorred_job.start()
    assert wait_for_status(errorred_job, JobStatus.ERROR, 10)


def test_message_error_handling(dispatcher: Dispatcher):
    message_job = dispatcher.create_job(MessageMockJob.job_path())
    message_job.start()
    redis: MockRedis = message_job.redis
    run_id = message_job.run.id

    message_id = str(uuid4())
    message = {'method': 'error', 'message_id': message_id}
    redis.publish(run_id, json.dumps(message))

    sleep(1)

    raw_response = redis.hget(run_id, message_id)
    assert raw_response is not None
    response = json.loads(raw_response)
    message_job.stop()
    assert response['status'] == 'error'


def test_message_response(dispatcher: Dispatcher):
    message_job = dispatcher.create_job(MessageMockJob.job_path())
    message_job.start()
    redis: MockRedis = message_job.redis
    run_id = message_job.run.id

    message_id = str(uuid4())
    message = {'method': 'repeat', 'message_id': message_id, 'params': {'payload': 'foo'}}
    redis.publish(run_id, json.dumps(message))

    sleep(1)

    raw_response = redis.hget(run_id, message_id)
    assert raw_response is not None
    response = json.loads(raw_response)
    message_job.stop()
    assert response['status'] == 'ok'
    assert response['response'] == 'foo'


def test_message_stop(dispatcher: Dispatcher):
    message_job = dispatcher.create_job(MessageMockJob.job_path())
    message_job.start()
    redis: MockRedis = message_job.redis
    run_id = message_job.run.id

    message_id = str(uuid4())
    message = {'method': 'stop', 'message_id': message_id}
    redis.publish(run_id, json.dumps(message))

    sleep(1)

    raw_response = redis.hget(run_id, message_id)
    assert raw_response is not None
    response = json.loads(raw_response)
    assert response['status'] == 'ok'

    assert wait_for_status(message_job, JobStatus.STOPPED)
