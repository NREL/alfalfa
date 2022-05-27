import os
from pathlib import Path

import pytest

from alfalfa_worker.dispatcher import Dispatcher
from tests.worker.lib.mock_run_manager import MockRunManager


@pytest.fixture
def dispatcher(tmp_path: Path):
    run_dir = tmp_path / 'runs'
    s3_dir = tmp_path / 's3'
    os.environ['RUN_DIR'] = str(run_dir)
    dispatcher = Dispatcher()
    dispatcher.run_manager = MockRunManager(run_dir, s3_dir)
    yield dispatcher
