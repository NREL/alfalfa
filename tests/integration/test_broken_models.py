import datetime

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient
from alfalfa_client.lib import AlfalfaException, create_zip


@pytest.mark.integration
def test_broken_models(broken_model_path):
    alfalfa = AlfalfaClient(host='http://localhost')
    with pytest.raises(AlfalfaException):
        run_id = alfalfa.submit(str(broken_model_path))
        alfalfa.start(
            run_id,
            external_clock=True,
            start_datetime=datetime.datetime(2019, 1, 2, 0, 2, 0),
            end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0))

        for _ in range(5):
            alfalfa.advance(run_id)

        alfalfa.stop(run_id)


@pytest.mark.integration
def test_broken_python_models(alfalfa: AlfalfaClient, broken_workflow_name):
    model_zip_path = create_zip("tests/integration/broken_models/small_office/measures",
                                "tests/integration/broken_models/small_office/weather",
                                "tests/integration/broken_models/small_office/small_office.osm",
                                f"tests/integration/broken_models/small_office/{broken_workflow_name}")
    with pytest.raises(AlfalfaException):
        run_id = alfalfa.submit(model_zip_path)
        alfalfa.start(
            run_id,
            external_clock=True,
            start_datetime=datetime.datetime(2019, 1, 2, 0, 2, 0),
            end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0))

        for _ in range(5):
            alfalfa.advance(run_id)

        alfalfa.stop(run_id)
