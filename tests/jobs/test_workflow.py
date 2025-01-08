import datetime
from pathlib import Path

import pytest

from alfalfa_worker.jobs.step_run_base import ClockSource
from alfalfa_worker.lib.enums import RunStatus, SimType
from alfalfa_worker.lib.job import JobStatus
from tests.worker.lib.mock_dispatcher import MockDispatcher
from tests.worker.utilities import (
    send_message_and_wait,
    wait_for_job_status,
    wait_for_run_status
)


@pytest.mark.docker
def test_simple_internal_clock(mock_dispatcher: MockDispatcher, model_path: Path):
    model = mock_dispatcher.run_manager.create_model(model_path)

    if model_path.is_dir():
        create_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.openstudio.create_run.CreateRun", {'model_id': model.ref_id})
    else:
        create_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.modelica.create_run.CreateRun", {'model_id': model.ref_id})

    run = create_run_job.run

    wait_for_job_status(create_run_job, JobStatus.STOPPED)
    wait_for_run_status(run, RunStatus.READY)

    params = {
        "run_id": run.ref_id,
        "external_clock": False,
        "start_datetime": str(datetime.datetime(2019, 1, 2, 0, 0, 0)),
        "end_datetime": str(datetime.datetime(2019, 1, 3, 0, 0, 0)),
        "timescale": "5",
        "realtime": False
    }

    if run.sim_type == SimType.OPENSTUDIO:
        step_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.openstudio.step_run.StepRun", params)
    else:
        step_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.modelica.step_run.StepRun", params)
    assert step_run_job.options.clock_source == ClockSource.INTERNAL
    run = step_run_job.run
    wait_for_job_status(step_run_job, JobStatus.RUNNING)
    wait_for_run_status(run, RunStatus.RUNNING)

    send_message_and_wait(step_run_job, 'stop', timeout=20)
    wait_for_job_status(step_run_job, JobStatus.STOPPED)
    wait_for_run_status(run, RunStatus.COMPLETE)


@pytest.mark.docker
def test_simple_external_clock(mock_dispatcher: MockDispatcher, model_path: Path):
    model = mock_dispatcher.run_manager.create_model(model_path)

    if model_path.is_dir():
        create_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.openstudio.create_run.CreateRun", {'model_id': model.ref_id})
    else:
        create_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.modelica.create_run.CreateRun", {'model_id': model.ref_id})
    run = create_run_job.run

    wait_for_run_status(run, RunStatus.READY)
    start_dt = datetime.datetime(2019, 1, 2, 0, 2, 0)
    params = {
        "run_id": run.ref_id,
        "external_clock": True,
        "start_datetime": str(start_dt),
        "end_datetime": str(datetime.datetime(2019, 1, 3, 0, 0, 0)),
        "timescale": "1",
        "realtime": False
    }

    if run.sim_type == SimType.OPENSTUDIO:
        step_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.openstudio.step_run.StepRun", params)
    else:
        step_run_job = mock_dispatcher.start_job("alfalfa_worker.jobs.modelica.step_run.StepRun", params)
    run = step_run_job.run

    wait_for_run_status(run, RunStatus.RUNNING, timeout=60)
    wait_for_job_status(step_run_job, JobStatus.WAITING)

    # -- Assert model gets to expected start time
    assert start_dt == run.sim_time
    updated_dt = start_dt

    for _ in range(10):

        # -- Advance a single time step
        send_message_and_wait(step_run_job, 'advance')

        # The above should hold in advance state.
        wait_for_job_status(step_run_job, JobStatus.WAITING)
        updated_dt += datetime.timedelta(minutes=1)
        assert updated_dt == run.sim_time

    # Shut down
    send_message_and_wait(step_run_job, 'stop', timeout=20)
    wait_for_job_status(step_run_job, JobStatus.STOPPED)
    wait_for_run_status(run, RunStatus.COMPLETE)
