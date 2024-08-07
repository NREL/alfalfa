from datetime import datetime, timedelta

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient

from tests.integration.conftest import prepare_model

##################################################################################################
# The is a test of the simple_thermostat.fmu,
# which represents a simplified air temperature controller.
#
# The inputs oveWriMeasuredTemp_u and TsetPoint_u represent the measured air temperature,
# and the desired control setpoint respectively.
#
# The output, rea, represents the control output signal.
#
# Modelica source code of the simple_thermostat.fmu is available here: <todo: add link to source>
##################################################################################################


@pytest.fixture
def simple_thermostat_run_id(alfalfa: AlfalfaClient):
    fmu_path = prepare_model('simple_thermostat.fmu')
    run_id = alfalfa.submit(fmu_path)

    alfalfa.wait(run_id, "ready")

    yield run_id

    alfalfa.stop(run_id)
    alfalfa.wait(run_id, "complete")


@pytest.mark.integration
def test_io_with_external_clock(alfalfa: AlfalfaClient, simple_thermostat_run_id):
    run_id = simple_thermostat_run_id

    current_datetime = datetime(2019, 1, 1)

    alfalfa.start(
        run_id,
        external_clock=True,
        start_datetime=current_datetime,
        end_datetime=datetime(2019, 1, 1, 0, 5),
        timescale=5
    )
    alfalfa.wait(run_id, "running")

    # Simulation is running, but time should still be at 0
    model_time = alfalfa.get_sim_time(run_id)
    assert current_datetime == model_time

    # If outputs are requested before the simulation is advanced,
    # there will be an error.
    # See issue https://github.com/NREL/alfalfa/issues/119
    current_datetime += timedelta(minutes=1)
    alfalfa.advance([run_id])
    model_time = alfalfa.get_sim_time(run_id)
    assert current_datetime == model_time

    # Having not set any inputs the fmu will be at the initial state.
    # The control signal output "rea" is at 0.0
    outputs = alfalfa.get_outputs(run_id)
    rea = outputs.get("rea")
    assert rea == pytest.approx(0.0)

    # Attempt to override the measured temp (ie zone temperature),
    # and the setpoint, such that zone temperature is over setpoint.
    alfalfa.set_inputs(run_id, {"oveWriMeasuredTemp_u": 303.15, "oveWriSetPoint_u": 294.15})

    # Advance time, outputs will not be updated until advance happens.
    # Should this limitation be considered a bug?
    # Note that boptest advance and set input apis are combined,
    # so that there is no method to set inputs without advancing
    current_datetime += timedelta(minutes=1)
    alfalfa.advance([run_id])
    model_time = alfalfa.get_sim_time(run_id)
    assert current_datetime == model_time

    # When temperature is over setpoint controller returns 0.0
    outputs = alfalfa.get_outputs(run_id)
    rea = outputs.get("rea")
    assert rea == pytest.approx(0.0)

    # Now override the measured (zone) temperature such that it is below setpoint
    alfalfa.set_inputs(run_id, {"oveWriMeasuredTemp_u": 283.15, "oveWriSetPoint_u": 294.15})

    current_datetime += timedelta(minutes=1)
    alfalfa.advance([run_id])
    model_time = alfalfa.get_sim_time(run_id)
    assert current_datetime == model_time

    # When temperature is below setpoint controller returns 1.0
    outputs = alfalfa.get_outputs(run_id)
    rea = outputs.get("rea")
    assert rea == pytest.approx(1.0)

    # Test the control signal override
    alfalfa.set_inputs(run_id, {"oveWriActuatorSignal_u": 0.0})
    current_datetime += timedelta(minutes=1)
    alfalfa.advance([run_id])
    model_time = alfalfa.get_sim_time(run_id)
    assert current_datetime == model_time
    outputs = alfalfa.get_outputs(run_id)
    rea = outputs.get("rea")
    assert rea == pytest.approx(0.0)
