import datetime

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient

from tests.integration.conftest import prepare_model


@pytest.mark.integration
def test_python_environment():
    zip_file_path = prepare_model('small_office')
    alfalfa = AlfalfaClient(host='http://localhost')
    model_id = alfalfa.submit(zip_file_path)

    alfalfa.wait(model_id, "ready")
    start_dt = datetime.datetime(2019, 1, 2, 0, 2, 0)
    alfalfa.start(
        model_id,
        external_clock=False,
        start_datetime=start_dt,
        end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0),
        timescale=1
    )

    alfalfa.wait(model_id, "running")

    alfalfa.advance([model_id])

    alfalfa.stop(model_id)
    alfalfa.wait(model_id, "complete")
