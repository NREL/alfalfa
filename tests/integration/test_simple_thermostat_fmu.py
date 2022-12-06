import os
from datetime import datetime, timedelta
from unittest import TestCase

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient

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


@pytest.mark.integration
class TestSimpleThermostat(TestCase):

    def setUp(self):
        self.alfalfa = AlfalfaClient(host='http://localhost')
        fmu_path = os.path.join(os.path.dirname(__file__), 'models', 'simple_thermostat.fmu')
        self.model_id = self.alfalfa.submit(fmu_path)

        self.alfalfa.wait(self.model_id, "ready")

        self.current_datetime = datetime(2019, 1, 1)

        self.alfalfa.start(
            self.model_id,
            external_clock=True,
            start_datetime=self.current_datetime,
            end_datetime=datetime(2019, 1, 1, 0, 5),
            timescale=5
        )
        self.alfalfa.wait(self.model_id, "running")

    def test_io_with_external_clock(self):
        # Simulation is running, but time should still be at 0
        model_time = self.alfalfa.get_sim_time(self.model_id)
        assert self.current_datetime == model_time

        # If outputs are requested before the simulation is advanced,
        # there will be an error.
        # See issue https://github.com/NREL/alfalfa/issues/119
        self.current_datetime += timedelta(minutes=1)
        self.alfalfa.advance([self.model_id])
        model_time = self.alfalfa.get_sim_time(self.model_id)
        assert self.current_datetime == model_time

        # Having not set any inputs the fmu will be at the initial state.
        # The control signal output "rea" is at 0.0
        outputs = self.alfalfa.get_outputs(self.model_id)
        rea = outputs.get("rea")
        assert rea == pytest.approx(0.0)

        # Attempt to override the measured temp (ie zone temperature),
        # and the setpoint, such that zone temperature is over setpoint.
        self.alfalfa.set_inputs(self.model_id, {"oveWriMeasuredTemp_u": 303.15, "oveWriSetPoint_u": 294.15})

        # Advance time, outputs will not be updated until advance happens.
        # Should this limitation be considered a bug?
        # Note that boptest advance and set input apis are combined,
        # so that there is no method to set inputs without advancing
        self.current_datetime += timedelta(minutes=1)
        self.alfalfa.advance([self.model_id])
        model_time = self.alfalfa.get_sim_time(self.model_id)
        assert self.current_datetime == model_time

        # When temperature is over setpoint controller returns 0.0
        outputs = self.alfalfa.get_outputs(self.model_id)
        rea = outputs.get("rea")
        assert rea == pytest.approx(0.0)

        # Now override the measured (zone) temperature such that it is below setpoint
        self.alfalfa.set_inputs(self.model_id, {"oveWriMeasuredTemp_u": 283.15, "oveWriSetPoint_u": 294.15})

        self.current_datetime += timedelta(minutes=1)
        self.alfalfa.advance([self.model_id])
        model_time = self.alfalfa.get_sim_time(self.model_id)
        assert self.current_datetime == model_time

        # When temperature is below setpoint controller returns 1.0
        outputs = self.alfalfa.get_outputs(self.model_id)
        rea = outputs.get("rea")
        assert rea == pytest.approx(1.0)

        # Test the control signal override
        self.alfalfa.set_inputs(self.model_id, {"oveWriActuatorSignal_u": 0.0})
        self.current_datetime += timedelta(minutes=1)
        self.alfalfa.advance([self.model_id])
        model_time = self.alfalfa.get_sim_time(self.model_id)
        assert self.current_datetime == model_time
        outputs = self.alfalfa.get_outputs(self.model_id)
        rea = outputs.get("rea")
        assert rea == pytest.approx(0.0)

    def tearDown(self):
        self.alfalfa.stop(self.model_id)
        self.alfalfa.wait(self.model_id, "complete")
