from pyenergyplus.plugin import EnergyPlusPlugin
import sklearn

class SimplePlugin(EnergyPlusPlugin):
    def __init__(self) -> None:
        super().__init__()

    def on_begin_timestep_before_predictor(self, state):
        return 0
