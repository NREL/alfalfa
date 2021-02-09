import os
import datetime
import pytest
from unittest import TestCase
from time import sleep
from alfalfa_client.alfalfa_client import AlfalfaClient


@pytest.mark.integration
class TestSmallOfficeOSM(TestCase):

    # def test_simple_internal_clock(self):
    #     alfalfa = AlfalfaClient(url='http://localhost')
    #     fmu_path = os.path.join(os.path.dirname(__file__), 'models', 'small_office.osm')
    #     model_id = alfalfa.submit(fmu_path)
    #
    #     alfalfa.wait(model_id, "Stopped")
    #
    #     alfalfa.start(
    #         model_id,
    #         external_clock="false",
    #         start_datetime=datetime.datetime(2019, 1, 2, 0, 0, 0),
    #         end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0),
    #         timescale=5
    #     )
    #
    #     alfalfa.wait(model_id, "Running")
    #     alfalfa.stop(model_id)
    #     alfalfa.wait(model_id, "Stopped")

    def test_simple_external_clock(self):
        alfalfa = AlfalfaClient(url='http://localhost')
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'small_office.osm')
        model_id = alfalfa.submit(model_path)

        alfalfa.wait(model_id, "Stopped")
        start_dt = datetime.datetime(2019, 1, 2, 0, 2, 0)
        alfalfa.start(
            model_id,
            external_clock="true",
            start_datetime=start_dt,
            end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0),
        )

        alfalfa.wait(model_id, "Running")

        # -- Assert model gets to expected start time
        model_time = alfalfa.get_sim_time(model_id)
        assert start_dt.strftime("%Y-%m-%d %H:%M") in model_time
        updated_dt = start_dt

        for i in range(10):
            alfalfa.advance(model_id)

            # We currently sleep here since there is no way for us to
            # know externally (client side) whether or not the E+ simulation
            # has finished its advance step.
            sleep(5)
            model_time = alfalfa.get_sim_time(model_id)
            updated_dt += datetime.timedelta(minutes=1)
            assert updated_dt.strftime("%Y-%m-%d %H:%M") in model_time
