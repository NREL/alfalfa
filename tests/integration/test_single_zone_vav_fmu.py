import os
import pytest
from unittest import TestCase
from alfalfa_client import AlfalfaClient


@pytest.mark.integration
class TestSingleZoneVAVFMU(TestCase):

    def test_simple_internal_clock(self):
        alfalfa = AlfalfaClient(url='http://localhost')
        fmu_path = os.path.join(os.path.dirname(__file__), 'models', 'single_zone_vav.fmu')
        model_id = alfalfa.submit(fmu_path)

        alfalfa.wait(model_id, "Stopped")

        alfalfa.start(
            model_id,
            external_clock="false",
            start_datetime=0,
            end_datetime=1000,
            timescale=5
        )

        alfalfa.wait(model_id, "Running")
        alfalfa.stop(model_id)
        alfalfa.wait(model_id, "Stopped")
