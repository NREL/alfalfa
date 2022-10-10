from datetime import datetime, timedelta
from math import ceil
from time import sleep

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient
from alfalfa_client.lib import AlfalfaException

from tests.integration.conftest import prepare_model

MODEL_COUNT = 6
WORKER_COUNT = 2


@pytest.fixture
def alfalfa_client():
    yield AlfalfaClient(url='http://localhost')


@pytest.fixture
def models(alfalfa_client: AlfalfaClient):

    MODEL_PATHS = []
    MODEL_PATHS.append('simple_thermostat.fmu')
    MODEL_PATHS.append('single_zone_vav.fmu')
    MODEL_PATHS.append('refrig_case_osw')
    MODEL_PATHS.append('small_office')

    model_ids = []

    for i in range(ceil(MODEL_COUNT / WORKER_COUNT)):
        upload_paths = []
        for k in range(min(WORKER_COUNT, MODEL_COUNT - WORKER_COUNT * i)):
            model_path = MODEL_PATHS[(i * WORKER_COUNT + k) % len(MODEL_PATHS)]
            model_path = prepare_model(model_path)

            upload_paths.append(model_path)
        model_ids.append(alfalfa_client.submit_many(upload_paths))

    yield model_ids

    stop_ids = []

    for model_id in [model_id for sublist in model_ids for model_id in sublist]:
        exception = None
        try:
            status = alfalfa_client.status(model_id)
            if status == "RUNNING":
                stop_ids.append(model_id)
        except AlfalfaException as e:
            exception = e
    if len(stop_ids) > 0:
        alfalfa_client.stop_many(stop_ids)
    if exception:
        raise exception


@pytest.mark.scale
def test_multiple_workers_simple_external_clock(models, alfalfa_client: AlfalfaClient):

    for model_ids in models:
        start_time = datetime(2019, 1, 2, 0, 0, 0)

        params = {
            "external_clock": True,
            "start_datetime": start_time,
            "end_datetime": datetime(2019, 1, 3, 0, 0, 0)
        }
        alfalfa_client.start_many(model_ids, **params)

        calculated_model_time = start_time

        for _ in range(10):
            alfalfa_client.advance(model_ids)
            calculated_model_time += timedelta(minutes=1)
            for model_id in model_ids:
                # -- Assert model gets to expected start time
                model_time = alfalfa_client.get_sim_time(model_id)
                assert calculated_model_time.strftime("%Y-%m-%d %H:%M") in model_time

        alfalfa_client.stop_many(model_ids)


@pytest.mark.scale
def test_multiple_workers_simple_internal_clock(models, alfalfa_client: AlfalfaClient):

    for model_ids in models:
        start_time = datetime(2019, 1, 2, 0, 0, 0)

        params = {
            "internal_clock": True,
            "start_datetime": start_time,
            "end_datetime": datetime(2019, 1, 2, 0, 5, 0),
            "timescale": 5
        }
        alfalfa_client.start_many(model_ids, **params)

        calculated_model_time = start_time

        sleep(90)
        calculated_model_time += timedelta(minutes=5)
        for model_id in model_ids:
            # -- Assert model gets to expected start time
            model_time = alfalfa_client.get_sim_time(model_id)
            assert calculated_model_time.strftime("%Y-%m-%d %H:%M") in model_time

        alfalfa_client.stop_many(model_ids)
