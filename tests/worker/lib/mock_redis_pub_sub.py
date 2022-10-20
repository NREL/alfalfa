from queue import Empty, SimpleQueue


class MockRedisPubSub():

    def __init__(self):
        self.messages: SimpleQueue = SimpleQueue()
        self.channels = []

    def get_message(self):
        message = None
        try:
            message = self.messages.get(False)
            return message
        except Empty:
            return message

    def subscribe(self, channel: str):
        self.channels.append(channel)
