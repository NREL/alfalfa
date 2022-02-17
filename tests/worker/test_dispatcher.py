import json

from unittest import TestCase
from alfalfa_worker.dispatcher import Dispatcher
from alfalfa_worker.worker_fmu.worker import WorkerFmu
from alfalfa_worker.worker_openstudio.worker import WorkerOpenStudio
from tests.worker.helpers.message_mock import MessageMock


class TestValidInit(TestCase):
    def test_valid_init(self):
        dispatcher = Dispatcher()
        self.assertTrue(isinstance(dispatcher, Dispatcher))

    def test_worker_add_site(self):
        dispatcher = Dispatcher()

        # This is a mocked message, if the queue changes, this needs to be updated
        # to support the new format of the queue messages.
        # TODO: make the body of the messages at a minimum a dictionary, or create a helper method
        message_stub = MessageMock({
            "body": json.dumps(
                {
                    "op": "InvokeAction",
                    "action": "init",
                    "model_name": "a/file/model.fmu",
                    "upload_id": "id_123"
                })
        })
        klass = dispatcher.process_message(message_stub)
        self.assertTrue(isinstance(klass, WorkerFmu))

        message_stub = MessageMock({
            "body": json.dumps(
                {
                    "op": "InvokeAction",
                    "action": "init",
                    "model_name": "a/file/model.OSW",
                    "upload_id": "id_456"
                })
        })
        klass = dispatcher.process_message(message_stub)
        self.assertTrue(isinstance(klass, WorkerOpenStudio))

    def test_worker_run_site(self):
        # {'id': '58244900-9039-11ec-87d0-acde48001122', 'op': 'InvokeAction', 'action': 'runSite', 'timescale': '1', 'startDatetime': '2019-01-02 00:02:00', 'endDatetime': '2019-01-03 00:00:00', 'realtime': 'undefined', 'externalClock': 'false'}
        pass
