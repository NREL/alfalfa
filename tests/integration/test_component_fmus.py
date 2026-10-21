# These FMUs (Boiler_EC.fmu, BuriedPipePair_FMU.fmu, Chiller_Carnot_y_FMU.fmu)
# are standalone Modelica component models -- not BOPTEST-style wrapped test
# cases -- generated using the compilation workflow in
# https://github.com/NatLabRockies/FMU-compilation-workbench/tree/develop
#
# They are used here to confirm Alfalfa can upload, run, and expose live
# input/output points (including declared input value ranges) for plain
# component FMUs of this shape.
from datetime import datetime, timedelta

import pytest
import requests
from alfalfa_client.alfalfa_client import AlfalfaClient

from tests.integration.conftest import prepare_model

# Each model's inputs/outputs and, where the FMU declares one, an input's
# valid write range (min/max), as read directly from its modelDescription.xml.
COMPONENT_MODELS = [
    {
        "file": "Boiler_EC.fmu",
        "inputs": ["inlet.forward.T", "inlet.m_flow", "y"],
        "outputs": ["outlet.forward.T", "outlet.m_flow"],
        "ranged_input": {"name": "inlet.forward.T", "min": 1.0, "max": 1e4},
        "write_input": {"name": "y", "value": 0.5}
    },
    {
        "file": "BuriedPipePair_FMU.fmu",
        "inputs": ["T_in_ret", "T_in_sup", "m_flow_ret", "m_flow_sup"],
        "outputs": ["Q_ret", "Q_sup", "T_out_ret", "T_out_sup"],
        "ranged_input": None,
        "write_input": {"name": "m_flow_sup", "value": 0.5}
    },
    {
        "file": "Chiller_Carnot_y_FMU.fmu",
        "inputs": ["T_in_con", "T_in_eva", "m_flow_con", "m_flow_eva", "y"],
        "outputs": ["COP", "P", "QCon_flow", "QEva_flow", "T_out_con", "T_out_eva"],
        "ranged_input": {"name": "y", "min": 0.0, "max": 1.0},
        # A modest part-load ratio -- jumping straight from the FMU's 0.0
        # start value to a large part-load ratio in a single step can make
        # this idealized Carnot-cycle model's solver fail to converge.
        "write_input": {"name": "y", "value": 0.1}
    }
]


@pytest.fixture
def base_url(alfalfa_host: str):
    return f"{alfalfa_host}/api/v2"


@pytest.mark.integration
@pytest.mark.parametrize("model", COMPONENT_MODELS, ids=lambda model: model["file"])
def test_component_fmu_runs_and_reports_results(alfalfa: AlfalfaClient, base_url, model):
    """Upload each component FMU, let it run for a couple of simulated
    minutes on Alfalfa's internal clock, and confirm every declared output
    point comes back with a real result."""
    run_id = alfalfa.submit(prepare_model(model["file"]))

    start_datetime = datetime(2019, 1, 1, 0, 0, 0)
    end_datetime = start_datetime + timedelta(minutes=2)
    alfalfa.start(run_id, start_datetime=start_datetime, end_datetime=end_datetime, external_clock=False, timescale=10)

    # Internal clock: Alfalfa advances the simulation on its own; wait for it to finish.
    alfalfa.wait(run_id, "complete", timeout=120)
    assert alfalfa.get_sim_time(run_id) == end_datetime

    inputs = alfalfa.get_inputs(run_id)
    for name in model["inputs"]:
        assert name in inputs, f"Expected input '{name}' was not found on the run"

    outputs = alfalfa.get_outputs(run_id)
    for name in model["outputs"]:
        assert name in outputs, f"Missing output '{name}' -- no simulation results were produced"
        assert outputs[name] is not None, f"Output '{name}' has no value"

    # Confirm any declared input range from the FMU's variable metadata is
    # surfaced through the REST API (used to enforce/display write limits in the UI).
    ranged_input = model["ranged_input"]
    if ranged_input:
        response = requests.get(f"{base_url}/runs/{run_id}/points")
        response.raise_for_status()
        points_by_name = {point["name"]: point for point in response.json()["payload"]}
        point = points_by_name[ranged_input["name"]]
        assert point["min"] == pytest.approx(ranged_input["min"])
        assert point["max"] == pytest.approx(ranged_input["max"])


@pytest.mark.integration
@pytest.mark.parametrize("model", COMPONENT_MODELS, ids=lambda model: model["file"])
def test_component_fmu_input_writes(alfalfa: AlfalfaClient, model):
    """Verify that values can be written into a run's INPUT points while the
    simulation is advancing -- i.e. sending signals into a run -- and that
    the model keeps producing output values in response."""
    run_id = alfalfa.submit(prepare_model(model["file"]))

    start_datetime = datetime(2019, 1, 1, 0, 0, 0)
    end_datetime = start_datetime + timedelta(minutes=2)
    alfalfa.start(run_id, start_datetime=start_datetime, end_datetime=end_datetime, external_clock=True)
    alfalfa.wait(run_id, "running")

    write_input = model["write_input"]
    alfalfa.set_inputs(run_id, {write_input["name"]: write_input["value"]})

    for _ in range(2):
        alfalfa.advance(run_id)

    outputs = alfalfa.get_outputs(run_id)
    assert outputs, "No output points were found on the run"
    for name, value in outputs.items():
        assert value is not None, f"Output '{name}' has no value after writing an input"

    alfalfa.stop(run_id)
    alfalfa.wait(run_id, "complete")
