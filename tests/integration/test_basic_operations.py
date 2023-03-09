from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient, SiteID


@pytest.mark.integration
def test_simple_internal_clock(alfalfa: AlfalfaClient, ref_id: SiteID):
    alfalfa.wait(ref_id, "ready")

    end_datetime = datetime(2019, 1, 2, 0, 2, 0)
    alfalfa.start(
        ref_id,
        external_clock=False,
        start_datetime=datetime(2019, 1, 2, 0, 0, 0),
        end_datetime=end_datetime,
        timescale=10
    )

    # Wait for model to complete
    alfalfa.wait(ref_id, "complete")
    model_time = alfalfa.get_sim_time(ref_id)
    assert end_datetime == model_time


@pytest.mark.integration
def test_simple_external_clock(alfalfa: AlfalfaClient, ref_id: SiteID):
    alfalfa.wait(ref_id, "ready")
    start_dt = datetime(2019, 1, 2, 23, 55, 0)
    alfalfa.start(
        ref_id,
        external_clock=True,
        start_datetime=start_dt,
        end_datetime=datetime(2019, 1, 3, 1, 0, 0)
    )

    alfalfa.wait(ref_id, "running")

    # -- Assert model gets to expected start time
    model_time = alfalfa.get_sim_time(ref_id)
    assert start_dt == model_time
    updated_dt = start_dt

    for _ in range(2):
        # -- Advance a single time step
        alfalfa.advance(ref_id)

        model_time = alfalfa.get_sim_time(ref_id)
        updated_dt += timedelta(minutes=1)
        assert updated_dt == model_time

    # Shut down
    alfalfa.stop(ref_id)
    alfalfa.wait(ref_id, "complete")


@pytest.mark.integration
def test_alias(alfalfa: AlfalfaClient):
    ref_id = str(uuid4())
    alfalfa.set_alias("test", ref_id)
    assert alfalfa.get_alias("test") == ref_id
