import os
import datetime
import pytest
from unittest import TestCase
from alfalfa_client.alfalfa_client import AlfalfaClient


@pytest.mark.integration
class TestSmallOfficeOSM(TestCase):

    def test_simple_internal_clock(self):
        alfalfa = AlfalfaClient(url='http://localhost')
        fmu_path = os.path.join(os.path.dirname(__file__), 'models', 'small_office.osm')
        model_id = alfalfa.submit(fmu_path)

        alfalfa.wait(model_id, "Stopped")

        alfalfa.start(
            model_id,
            external_clock="false",
            start_datetime=datetime.datetime(2019, 1, 2, 0, 0, 0),
            end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0),
            timescale=5
        )

        alfalfa.wait(model_id, "Running")
        alfalfa.stop(model_id)
        alfalfa.wait(model_id, "Stopped")
