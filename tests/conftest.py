# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for alfalfa.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""


from pathlib import Path

import pytest

from alfalfa_worker.dispatcher import Dispatcher
from tests.worker.lib.mock_dispatcher import MockDispatcher


@pytest.fixture
def dispatcher(tmp_path: Path):
    """Regular dispatcher with MockRunManager.
    Use for running MockJobs locally"""
    run_dir = tmp_path / 'runs'
    tmp_path / 's3'
    dispatcher = Dispatcher(run_dir)
    yield dispatcher


@pytest.fixture
def mock_dispatcher(tmp_path: Path):
    """MockDispatcher with regular RunManager.
    Use for running regular jobs in Docker"""
    work_dir = (tmp_path / 'runs')
    work_dir.mkdir()
    dispatcher = MockDispatcher(work_dir)
    yield dispatcher
