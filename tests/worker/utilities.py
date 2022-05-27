import json
import time
from typing import Dict
from uuid import uuid4

from alfalfa_worker.lib.job import Job, JobStatus
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


def wait_for_status(job: Job, desired_status: JobStatus, timeout: int = 10):
    start_time = time.time()
    while timeout > time.time() - start_time:
        if job.status == desired_status:
            return True
        time.sleep(0.5)
    assert False, f"Desired Job Status: {desired_status} not reached. Current Status: {job.status}"
