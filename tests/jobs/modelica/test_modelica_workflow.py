from pathlib import Path
from time import sleep

import pytest

from alfalfa_worker.lib.job import JobStatus
from alfalfa_worker.lib.run import RunStatus
from tests.worker.lib.mock_dispatcher import MockDispatcher
from tests.worker.utilities import (
    send_message_and_wait,
    wait_for_job_status,
    wait_for_run_status
)


@pytest.mark.docker
def test_simple_internal_clock(mock_dispatcher: MockDispatcher, model_path: Path):
    upload_id, model_name = mock_dispatcher.add_model(model_path)

    create_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.modelica.CreateRun", {'upload_id': upload_id, 'model_name': model_name})
    run = create_run_job.run

    wait_for_job_status(create_run_job, JobStatus.STOPPED)
    wait_for_run_status(run, RunStatus.READY)

    params = {
        "run_id": run.id,
        "external_clock": False,
        "start_datetime": "0",
        "end_datetime": "1000",
        "timescale": "5",
        "realtime": None
    }

    step_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.modelica.StepRun", params)
    assert step_run_job.step_sim_type == "timescale"
    run = step_run_job.run
    wait_for_job_status(step_run_job, JobStatus.RUNNING)
    wait_for_run_status(run, RunStatus.RUNNING)

    send_message_and_wait(step_run_job, 'stop', timeout=60)
    wait_for_job_status(step_run_job, JobStatus.STOPPED)
    wait_for_run_status(run, RunStatus.COMPLETE)


@pytest.mark.docker
def test_simple_external_clock(mock_dispatcher: MockDispatcher, model_path: Path):
    upload_id, model_name = mock_dispatcher.add_model(model_path)

    create_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.modelica.CreateRun", {'upload_id': upload_id, 'model_name': model_name})
    run = create_run_job.run

    wait_for_run_status(run, RunStatus.READY)
    start_dt = 0
    params = {
        "run_id": run.id,
        "external_clock": True,
        "start_datetime": str(start_dt),
        "end_datetime": "1000",
        "timescale": "1",
        "realtime": None
    }
    step_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.modelica.StepRun", params)
    run = step_run_job.run

    wait_for_run_status(run, RunStatus.RUNNING)
    wait_for_job_status(step_run_job, JobStatus.WAITING)

    # -- Assert model gets to expected start time
    assert start_dt == run.sim_time
    updated_dt = start_dt

    for _ in range(2):

        # -- Advance a single time step
        send_message_and_wait(step_run_job, 'advance')

        # The above should hold in advance state.
        wait_for_job_status(step_run_job, JobStatus.WAITING)
        updated_dt += 60
        assert updated_dt == run.sim_time

    # -- Advance a single time step
    send_message_and_wait(step_run_job, 'advance')

    # The above should hold in advance state.
    sleep(65)
    updated_dt += 60
    assert updated_dt == run.sim_time

    # Shut down
    send_message_and_wait(step_run_job, 'stop', timeout=20)
    wait_for_job_status(step_run_job, JobStatus.STOPPED)
    wait_for_run_status(run, RunStatus.COMPLETE)
