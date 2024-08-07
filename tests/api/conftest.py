import os
from pathlib import Path

import pytest
from alfalfa_client import AlfalfaClient
from alfalfa_client.alfalfa_client import AlfalfaAPIException


@pytest.fixture
def base_url():
    return 'http://localhost/api/v2'


@pytest.fixture
def alfalfa_client():
    return AlfalfaClient()


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
