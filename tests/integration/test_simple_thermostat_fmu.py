import os
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
        self.alfalfa = AlfalfaClient(url='http://localhost')
        fmu_path = os.path.join(os.path.dirname(__file__), 'models', 'simple_thermostat.fmu')
        self.model_id = self.alfalfa.submit(fmu_path)

        self.alfalfa.wait(self.model_id, "READY")

        self.alfalfa.start(
            self.model_id,
            external_clock="true",
            start_datetime=0,
            end_datetime=10000,
            timescale=5
        )
        self.alfalfa.wait(self.model_id, "RUNNING")

    def test_io_with_external_clock(self):
        # Simulation is running, but time should still be at 0
        time = self.alfalfa.get_sim_time(self.model_id)
        assert float(time) == pytest.approx(0.0)

        # If outputs are requested before the simulation is advanced,
        # there will be an error.
        # See issue https://github.com/NREL/alfalfa/issues/119
        self.alfalfa.advance([self.model_id])
        time = self.alfalfa.get_sim_time(self.model_id)
        assert float(time) == pytest.approx(60.0)

        # Having not set any inputs the fmu will be at the initial state.
        # The control signal output "rea" is at 0.0
        outputs = self.alfalfa.outputs(self.model_id)
        rea = outputs.get("rea")
        assert rea == pytest.approx(0.0)

        # Attempt to override the measured temp (ie zone temperature),
        # and the setpoint, such that zone temperature is over setpoint.
        self.alfalfa.setInputs(self.model_id, {"oveWriMeasuredTemp_u": 303.15, "oveWriSetPoint_u": 294.15})

        # Advance time, outputs will not be updated until advance happens.
        # Should this limitation be considered a bug?
        # Note that boptest advance and set input apis are combined,
        # so that there is no method to set inputs without advancing
        self.alfalfa.advance([self.model_id])
        time = self.alfalfa.get_sim_time(self.model_id)
        assert float(time) == pytest.approx(120.0)

        # When temperature is over setpoint controller returns 0.0
        outputs = self.alfalfa.outputs(self.model_id)
        rea = outputs.get("rea")
        assert rea == pytest.approx(0.0)

        # Now override the measured (zone) temperature such that it is below setpoint
        self.alfalfa.setInputs(self.model_id, {"oveWriMeasuredTemp_u": 283.15, "oveWriSetPoint_u": 294.15})

        self.alfalfa.advance([self.model_id])
        time = self.alfalfa.get_sim_time(self.model_id)
        assert float(time) == pytest.approx(180.0)

        # When temperature is below setpoint controller returns 1.0
        outputs = self.alfalfa.outputs(self.model_id)
        rea = outputs.get("rea")
        assert rea == pytest.approx(1.0)

        # Test the control signal override
        self.alfalfa.setInputs(self.model_id, {"oveWriActuatorSignal_u": 0.0})
        self.alfalfa.advance([self.model_id])
        time = self.alfalfa.get_sim_time(self.model_id)
        assert float(time) == pytest.approx(240.0)
        outputs = self.alfalfa.outputs(self.model_id)
        rea = outputs.get("rea")
        assert rea == pytest.approx(0.0)

    def tearDown(self):
        self.alfalfa.stop(self.model_id)
        self.alfalfa.wait(self.model_id, "COMPLETE")
