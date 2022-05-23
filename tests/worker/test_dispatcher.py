from unittest import TestCase

from alfalfa_worker.dispatcher import Dispatcher


class TestValidInit(TestCase):
    def test_valid_init(self):
        dispatcher = Dispatcher()
        self.assertTrue(isinstance(dispatcher, Dispatcher))
