# TODO

# Local imports
from alfalfa_worker.step_sim.model_advancer import ModelAdvancer


class FMUModelAdvancer(ModelAdvancer):
    def __init__(self):
        super(FMUModelAdvancer, self).__init__()
