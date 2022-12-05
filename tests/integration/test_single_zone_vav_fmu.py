import os
from time import sleep
from unittest import TestCase

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient


@pytest.mark.integration
class TestSingleZoneVAVFMU(TestCase):

    def test_simple_internal_clock(self):
        alfalfa = AlfalfaClient(host='http://localhost')
        fmu_path = os.path.join(os.path.dirname(__file__), 'models', 'single_zone_vav.fmu')
        model_id = alfalfa.submit(fmu_path)

        alfalfa.wait(model_id, "READY")

        end_time = 60 * 5
        alfalfa.start(
            model_id,
            external_clock=False,
            start_datetime=0,
            end_datetime=end_time,
            timescale=5
        )

        alfalfa.wait(model_id, "running")
        # wait for model to advance for 1 minute at timescale 5
        sleep(60)
        alfalfa.wait(model_id, "complete")
        model_time = alfalfa.get_sim_time(model_id)
        assert str(end_time) in model_time
