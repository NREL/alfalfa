# TODO

# Local imports
from worker.step_sim.model_advancer import ModelAdvancer


class FMUModelAdvancer(ModelAdvancer):
    def __init__(self):
        super(FMUModelAdvancer, self).__init__()
