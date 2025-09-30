import os
from datetime import datetime
from pathlib import Path

import pytest
from alfalfa_client import AlfalfaClient
from alfalfa_client.alfalfa_client import AlfalfaAPIException


@pytest.fixture
def base_url(alfalfa_host: str):
    return f'{alfalfa_host}/api/v2'


@pytest.fixture
def alfalfa_client(alfalfa_host: str):
    return AlfalfaClient(host=alfalfa_host)


@pytest.fixture
def model_path():
    return Path(os.path.dirname(__file__)) / "models" / "small_office"


@pytest.fixture
def model_id(alfalfa_client: AlfalfaClient, model_path):
    return alfalfa_client.upload_model(model_path)


@pytest.fixture
def run_id(alfalfa_client: AlfalfaClient, model_path):
    run_id = alfalfa_client.submit(model_path)
    yield run_id
    try:
        if alfalfa_client.status(run_id) not in ["COMPLETE", "ERROR", "STOPPING", "READY"]:
            alfalfa_client.stop(run_id)
    except AlfalfaAPIException:
        pass


@pytest.fixture
def started_run_id(alfalfa_client: AlfalfaClient, run_id):
    alfalfa_client.start(run_id, datetime(2020, 1, 1, 0, 0), datetime(2020, 1, 2, 0, 0), external_clock=True)
    yield run_id
