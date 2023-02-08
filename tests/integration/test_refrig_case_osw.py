import datetime
from unittest import TestCase

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient
from alfalfa_client.lib import AlfalfaException

from tests.integration.conftest import prepare_model


@pytest.mark.integration
class TestRefrigCaseOSW(TestCase):

    def test_invalid_start_conditions(self):
        zip_file_path = prepare_model('refrig_case_osw')
        alfalfa = AlfalfaClient(host='http://localhost')
        model_id = alfalfa.submit(zip_file_path)
        with pytest.raises(AlfalfaException):
            alfalfa.start(
                model_id,
                external_clock=False,
                start_datetime=datetime.datetime(2019, 1, 2, 0, 0, 0),
                end_datetime=datetime.datetime(2019, 1, 1, 0, 0, 0),
                timescale=5
            )

    def test_basic_io(self):
        zip_file_path = prepare_model('refrig_case_osw')
        alfalfa = AlfalfaClient(host='http://localhost')
        model_id = alfalfa.submit(zip_file_path)

        alfalfa.wait(model_id, "ready")
        alfalfa.start(
            model_id,
            external_clock=True,
            start_datetime=datetime.datetime(2019, 1, 2, 0, 2, 0),
            end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0)
        )

        alfalfa.wait(model_id, "running")

        inputs = alfalfa.get_inputs(model_id)
        assert "Test_Point_1" in inputs, "Test_Point_1 is in input points"
        inputs = {}
        inputs["Test_Point_1"] = 12

        alfalfa.set_inputs(model_id, inputs)

        outputs = alfalfa.get_outputs(model_id)
        assert "Test_Point_1" in outputs.keys(), "Echo point for Test_Point_1 is not in outputs"

        # -- Advance a single time step
        alfalfa.advance([model_id])

        outputs = alfalfa.get_outputs(model_id)
        assert outputs["Test_Point_1"] == pytest.approx(12), "Test_Point_1 value has not been processed by the model"

        # Shut down
        alfalfa.stop(model_id)
        alfalfa.wait(model_id, "complete")
