
from datetime import datetime
from time import sleep

import pytest

from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.lib.enums import RunStatus
from alfalfa_worker.lib.job import JobStatus
from tests.worker.jobs.step_run_mock_job import StepRunMockJob
from tests.worker.utilities import (
    send_message_and_wait,
    wait_for_job_status,
    wait_for_run_status
)


@pytest.fixture
def step_run_mock_job(dispatcher: Dispatcher):
    run = dispatcher.run_manager.create_empty_run()
    dispatcher.run_manager.checkin_run(run)

    params = {
        "run_id": run.ref_id,
        "external_clock": False,
        "start_datetime": str(datetime(2019, 1, 2, 0, 0, 0)),
        "end_datetime": str(datetime(2019, 1, 3, 0, 0, 0)),
        "timescale": "20",
        "realtime": False
    }

    yield dispatcher.create_job(StepRunMockJob.job_path(), params)


def test_timescale(step_run_mock_job: StepRunMockJob):

    step_run_mock_job.start()
    run = step_run_mock_job.run

    wait_for_job_status(step_run_mock_job, JobStatus.RUNNING)
    wait_for_run_status(run, RunStatus.RUNNING)

    first_time = run.sim_time

    sleep(10)

    assert run.sim_time > first_time

    send_message_and_wait(step_run_mock_job, 'stop')

    wait_for_job_status(step_run_mock_job, JobStatus.STOPPED)
    wait_for_run_status(run, RunStatus.COMPLETE)


def test_timescale_error(step_run_mock_job: StepRunMockJob):
    """Test that job will entered errored state if simulation step duration is too long
    relative to the timescale"""

    step_run_mock_job.start()
    run = step_run_mock_job.run

    wait_for_job_status(step_run_mock_job, JobStatus.RUNNING)
    wait_for_run_status(run, RunStatus.RUNNING)

    send_message_and_wait(step_run_mock_job, 'set_simulation_step_duration', {'simulation_step_duration': 6})

    wait_for_job_status(step_run_mock_job, JobStatus.ERROR)
    wait_for_run_status(run, RunStatus.ERROR)
