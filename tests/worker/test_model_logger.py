from unittest import TestCase

from alfalfa_worker.model_logger import ModelLogger


class TestModelLogger(TestCase):
    def test_init(self):
        ml = ModelLogger()
        self.assertIsNotNone(ml)
