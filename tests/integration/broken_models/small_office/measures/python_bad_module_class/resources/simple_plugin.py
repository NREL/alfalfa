from pyenergyplus.plugin import EnergyPlusPlugin


class SimplePlugin(EnergyPlusPlugin):
    def __init__(self) -> None:
        super().__init__()

        self.input_handle = None
        self.output_handle = None

    def on_begin_timestep_before_predictor(self, state):
        if self.input_handle is None:
            self.input_handle = self.api.exchange.get_global_handle(state, "input")
        if self.output_handle is None:
            self.output_handle = self.api.exchange.get_global_handle(state, "output")
        self.api.exchange.set_global_value(state, self.output_handle, self.api.exchange.get_global_value(state, self.input_handle))
        return 0
