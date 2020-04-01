from unittest import TestCase

from alfalfa_worker.step_sim.model_logger import ModelLogger


class TestModelLogger(TestCase):
    def test_init(self):
        ml = ModelLogger()
        self.assertIsNotNone(ml)
