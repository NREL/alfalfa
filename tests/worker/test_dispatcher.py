from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.jobs.openstudio.create_run import CreateRun
from alfalfa_worker.jobs.openstudio.step_run import StepRun
from alfalfa_worker.lib.job import JobStatus
from tests.worker.conftest import wait_for_status
from tests.worker.jobs.basic_mock_job import BasicMockJob


def test_valid_init(dispatcher):
    assert isinstance(dispatcher, Dispatcher)


def test_get_builtin_job(dispatcher):
    create_run_job = dispatcher.find_class('alfalfa_worker.jobs.openstudio.CreateRun')
    assert create_run_job == CreateRun


def test_get_from_job_get_path(dispatcher):
    step_run_job = dispatcher.find_class(StepRun.job_path())
    assert step_run_job == StepRun


def test_test_job_create_with_params(dispatcher):
    params = {'foo': 1, 'bar': 2}
    test_job = dispatcher.create_job(BasicMockJob.job_path(), params)
    assert test_job.foo == 1
    assert test_job.bar == 2
    assert isinstance(test_job, BasicMockJob)


def test_test_job_start(dispatcher):
    params = {'foo': 1, 'bar': 2}
    test_job = dispatcher.start_job(BasicMockJob.job_path(), params)
    wait_for_status(test_job, JobStatus.RUNNING)
    test_job.stop()
