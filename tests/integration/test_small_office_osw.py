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


@pytest.mark.integration
def test_io(alfalfa: AlfalfaClient):
    zip_file_path = prepare_model('small_office')
    site_id = alfalfa.submit(zip_file_path)

    alfalfa.wait(site_id, "ready")
    start_dt = datetime.datetime(2019, 1, 2, 0, 2, 0)
    alfalfa.start(
        site_id,
        external_clock=True,
        start_datetime=start_dt,
        end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0),
        timescale=1
    )

    inputs = alfalfa.get_inputs(site_id)
    outputs = alfalfa.get_outputs(site_id)

    # This is an Actuator
    assert "OfficeSmall HTGSETP_SCH_NO_OPTIMUM" in inputs
    # This is a Global Variable
    assert "Python Input" in inputs, "'Python Input' not found in 'inputs'"
    # This is an Output Variable
    assert "OfficeSmall HTGSETP_SCH_NO_OPTIMUM" in outputs.keys()
    # This is a Global Variable
    assert "Python Output" in outputs.keys(), "'Python Output' not found in 'outputs'"

    inputs = {"OfficeSmall HTGSETP_SCH_NO_OPTIMUM": 0, "Python Input": 20}
    alfalfa.set_inputs(site_id, inputs)

    for _ in range(5):
        alfalfa.advance(site_id)

        outputs = alfalfa.get_outputs(site_id)
        assert outputs["OfficeSmall HTGSETP_SCH_NO_OPTIMUM"] == pytest.approx(0)
        assert outputs["Python Output"] == pytest.approx(20), "'Python Output' has incorrect value"

    inputs = {"OfficeSmall HTGSETP_SCH_NO_OPTIMUM": None, "Python Input": 0}
    alfalfa.set_inputs(site_id, inputs)
    alfalfa.advance(site_id)

    outputs = alfalfa.get_outputs(site_id)
    assert outputs["OfficeSmall HTGSETP_SCH_NO_OPTIMUM"] != pytest.approx(0)
    assert outputs["Python Output"] == pytest.approx(0)

    alfalfa.stop(site_id)
    alfalfa.wait(site_id, "complete")
