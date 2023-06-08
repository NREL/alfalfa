from datetime import datetime

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient

from tests.integration.conftest import prepare_model


@pytest.mark.integration
def test_schedule_point_generation():
    alfalfa = AlfalfaClient('http://localhost')
    site_id = alfalfa.submit(prepare_model('schedule_model'))

    inputs = alfalfa.get_inputs(site_id)
    outputs = alfalfa.get_outputs(site_id)
    assert "CONSTANT HEATING" in inputs, "Constant Schedule input not generated"
    assert "COMPACT COOLING" in inputs, "Compact Schedule input not generated"
    assert "YEAR HEATING" in inputs, "Year Schedule input not generated"
    assert "RULESET COOLING" in inputs, "Rulseset Schedule input not generated"
    assert "FIXEDINTERVAL HEATING" in inputs, "Fixed Interval Schedule input not generated"

    assert "CONSTANT HEATING" in outputs.keys(), "Constant Schedule output not generated"
    assert "COMPACT COOLING" in outputs.keys(), "Compact Schedule output not generated"
    assert "YEAR HEATING" in outputs.keys(), "Year Schedule output not generated"
    assert "RULESET COOLING" in outputs.keys(), "Rulseset Schedule output not generated"
    assert "FIXEDINTERVAL HEATING" in outputs.keys(), "Fixed Interval Schedule output not generated"


@pytest.mark.integration
def test_schedule_override():
    alfalfa = AlfalfaClient('http://localhost')
    site_id = alfalfa.submit(prepare_model('schedule_model'))

    alfalfa.start(
        site_id,
        external_clock=True,
        start_datetime=datetime(2020, 1, 1, 0, 0),
        end_datetime=datetime(2020, 1, 2, 0, 0)
    )

    inputs = {
        "CONSTANT HEATING": 23.0,
        "COMPACT COOLING": 15.0,
        "YEAR HEATING": 23.0,
        "RULESET COOLING": 15.0,
        "FIXEDINTERVAL HEATING": 23.0
    }

    alfalfa.set_inputs(site_id, inputs)
    alfalfa.advance(site_id)

    outputs = alfalfa.get_outputs(site_id)
    assert inputs.items() <= outputs.items(), "Schedule override failed"

    alfalfa.stop(site_id)
