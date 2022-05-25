from typing import Dict, List

from tests.worker.lib.mock_redis_pub_sub import MockRedisPubSub


class MockRedis:
    hash: Dict[str, Dict[str, str]] = {}
    pubsubs: List[MockRedisPubSub] = []

    def hset(self, channel: str, key: str, value: str):
        if channel not in self.hash.keys():
            self.hash[channel] = {}
        self.hash[channel][key] = value

    def hget(self, channel: str, key: str):
        if channel not in self.hash.keys():
            return None
        if key not in self.hash[channel].keys():
            return None
        return self.hash[channel][key]

    def pubsub(self, **kwargs):
        pubsub = MockRedisPubSub()
        self.pubsubs.append(pubsub)
        return pubsub

    def publish(self, channel: str, data: str):
        message = {'channel': channel, 'data': data.encode('utf-8')}
        for pubsub in self.pubsubs:
            if channel in pubsub.channels:
                pubsub.messages.put(message)
