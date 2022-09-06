import datetime

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient

from tests.integration.conftest import create_zip


@pytest.mark.integration
def test_python_environment():
    zip_file_path = create_zip('small_office')
    alfalfa = AlfalfaClient(url='http://localhost')
    model_id = alfalfa.submit(zip_file_path)

    alfalfa.wait(model_id, "READY")
    start_dt = datetime.datetime(2019, 1, 2, 0, 2, 0)
    alfalfa.start(
        model_id,
        external_clock="false",
        start_datetime=start_dt,
        end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0),
        timescale=1
    )

    alfalfa.wait(model_id, "RUNNING")

    alfalfa.advance([model_id])

    alfalfa.stop(model_id)
    alfalfa.wait(model_id, "COMPLETE")
