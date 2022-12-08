import datetime

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient
from alfalfa_client.lib import AlfalfaException


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
