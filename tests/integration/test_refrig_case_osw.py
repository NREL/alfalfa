import datetime
from time import sleep
from unittest import TestCase

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient
from alfalfa_client.lib import AlfalfaException

from tests.integration.conftest import create_zip


@pytest.mark.integration
class TestRefrigCaseOSW(TestCase):

    def test_error_run(self):
        zip_file_path = create_zip('refrig_case_osw')
        alfalfa = AlfalfaClient(url='http://localhost')
        model_id = alfalfa.submit(zip_file_path)
        with pytest.raises(AlfalfaException):
            alfalfa.start(model_id)

    def test_simple_internal_clock(self):
        zip_file_path = create_zip('refrig_case_osw')
        alfalfa = AlfalfaClient(url='http://localhost')
        model_id = alfalfa.submit(zip_file_path)

        alfalfa.wait(model_id, "READY")

        alfalfa.start(
            model_id,
            external_clock="false",
            start_datetime=datetime.datetime(2019, 1, 2, 0, 0, 0),
            end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0),
            timescale=5
        )

        alfalfa.wait(model_id, "RUNNING")
        alfalfa.stop(model_id)
        alfalfa.wait(model_id, "COMPLETE")

    def test_simple_external_clock(self):
        zip_file_path = create_zip('refrig_case_osw')
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

        # -- Assert model gets to expected start time
        model_time = alfalfa.get_sim_time(model_id)
        assert start_dt.strftime("%Y-%m-%d %H:%M") in model_time
        updated_dt = start_dt

        # -- Advance a single time step
        alfalfa.advance([model_id])

        # The above should hold in advance state.
        sleep(5)
        model_time = alfalfa.get_sim_time(model_id)
        updated_dt += datetime.timedelta(minutes=1)
        # assert updated_dt.strftime("%Y-%m-%d %H:%M") in model_time

        # -- Advance a single time step
        alfalfa.advance([model_id])

        # The above should hold in advance state.
        sleep(65)
        model_time = alfalfa.get_sim_time(model_id)
        updated_dt += datetime.timedelta(minutes=1)
        # assert updated_dt.strftime("%Y-%m-%d %H:%M") in model_time

        # Shut down
        alfalfa.stop(model_id)
        alfalfa.wait(model_id, "COMPLETE")

    def test_basic_io(self):
        zip_file_path = create_zip('refrig_case_osw')
        alfalfa = AlfalfaClient(url='http://localhost')
        model_id = alfalfa.submit(zip_file_path)

        alfalfa.wait(model_id, "READY")
        alfalfa.start(
            model_id,
            external_clock="true",
            start_datetime=datetime.datetime(2019, 1, 2, 0, 2, 0),
            end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0)
        )

        alfalfa.wait(model_id, "RUNNING")

        inputs = alfalfa.inputs(model_id)
        assert "Test_Point_1" in inputs.keys(), "Test_Point_1 is in input points"
        inputs["Test_Point_1"] = 12

        alfalfa.setInputs(model_id, inputs)

        outputs = alfalfa.outputs(model_id)
        assert "Test_Point_1_Value" in outputs.keys(), "Echo point for Test_Point_1 is not in outputs"
        assert "Test_Point_1_Enable_Value" in outputs.keys(), "Echo point for Test_Point_1_Enable is not in outputs"

        # -- Advance a single time step
        alfalfa.advance([model_id])
        alfalfa.advance([model_id])

        outputs = alfalfa.outputs(model_id)
        assert int(outputs["Test_Point_1_Value"] == 12), "Test_Point_1 value has not been processed by the model"
        assert int(outputs["Test_Point_1_Enable_Value"] == 1), "Enable flag for Test_Point_1 is not set correctly"

        # Shut down
        alfalfa.stop(model_id)
        alfalfa.wait(model_id, "COMPLETE")
