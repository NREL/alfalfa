# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for alfalfa.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""


# @pytest.fixture(autouse=True)
# def env_setup(monkeypatch):
#     monkeypatch.setenv('WEB_REGISTRY_URI', '313781303390.dkr.ecr.us-east-1.amazonaws.com/queue/web')
#     monkeypatch.setenv('WORKER_REGISTRY_URI', '313781303390.dkr.ecr.us-east-1.amazonaws.com/queue/worker')
#     monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'user')
#     monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'password')
#     monkeypatch.setenv('NODE_ENV', 'production')
#     monkeypatch.setenv('S3_URL', 'http://localhost:9000')
#     monkeypatch.setenv('REDIS_HOST', 'redis')
#     monkeypatch.setenv('S3_BUCKET', 'alfalfa')
#     monkeypatch.setenv('JOB_QUEUE_URL', 'http://localhost:4100/queue/local-queue1')
#     monkeypatch.setenv('MONGO_URL', 'mongodb://localhost:27017/')
#     monkeypatch.setenv('MONGO_DB_NAME', 'alfalfa')
#     monkeypatch.setenv('REGION', 'us-west-1')

from pathlib import Path

import pytest

from alfalfa_worker.dispatcher import Dispatcher
from tests.worker.lib.mock_dispatcher import MockDispatcher
from tests.worker.lib.mock_run_manager import MockRunManager


@pytest.fixture
def dispatcher(tmp_path: Path):
    """Regular dispatcher with MockRunManager.
    Use for running MockJobs locally"""
    run_dir = tmp_path / 'runs'
    s3_dir = tmp_path / 's3'
    dispatcher = Dispatcher(run_dir)
    dispatcher.run_manager = MockRunManager(run_dir, s3_dir)
    yield dispatcher


@pytest.fixture
def mock_dispatcher(tmp_path: Path):
    """MockDispatcher with regular RunManager.
    Use for running regular jobs in Docker"""
    dispatcher = MockDispatcher(tmp_path)
    yield dispatcher
