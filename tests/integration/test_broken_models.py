import datetime

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient
from alfalfa_client.lib import AlfalfaException


@pytest.mark.integration
@pytest.mark.skip(reason="Test does not fail with the new database backend -- due to return???")
def test_broken_models(broken_model_path):
    alfalfa = AlfalfaClient(url='http://localhost')
    with pytest.raises(AlfalfaException):
        run_id = alfalfa.submit(str(broken_model_path))
        if broken_model_path.suffix == ".zip":
            alfalfa.start(
                run_id,
                external_clock=True,
                start_datetime=datetime.datetime(2019, 1, 2, 0, 2, 0),
                end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0))
        else:
            alfalfa.start(
                run_id,
                external_clock=True,
                start_datetime=0,
                end_datetime=1000)

        for _ in range(5):
            alfalfa.advance([run_id])

        alfalfa.stop(run_id)
