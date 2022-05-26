import os
import sys
import time
from pathlib import Path

import pytest

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.job import Job, JobStatus
from tests.worker.lib.mock_run_manager import MockRunManager


def wait_for_status(job: Job, desired_status: JobStatus, timeout: int = 10):
    start_time = time.time()
    while timeout > time.time() - start_time:
        if job.status == desired_status:
            return True
        time.sleep(0.5)
    print(f"{job.status} != {desired_status}", file=sys.stderr)
    assert False, f"Desired Job Status: {desired_status} not reached. Current Status: {job.status}"


@pytest.fixture
def dispatcher(tmp_path: Path):
    run_dir = tmp_path / 'runs'
    s3_dir = tmp_path / 's3'
    os.environ['RUN_DIR'] = str(run_dir)
    dispatcher = Dispatcher()
    dispatcher.run_manager = MockRunManager(run_dir, s3_dir)
    yield dispatcher
