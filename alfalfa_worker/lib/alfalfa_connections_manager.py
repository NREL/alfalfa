import os

import boto3
from mongoengine import connect
from redis import Redis

from alfalfa_worker.lib.singleton import Singleton


class AlafalfaConnectionsManager(metaclass=Singleton):

    def __init__(self) -> None:
        # Setup S3
        self.s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])
        self.s3_bucket = self.s3.Bucket(os.environ['S3_BUCKET'])

        # Mongo - connect using mongoengine
        connect(host=f"{os.environ['MONGO_URL']}/{os.environ['MONGO_DB_NAME']}", uuidrepresentation='standard')

        # Redis
        self.redis = Redis(host=os.environ['REDIS_HOST'])

        # Setup SQS
        self.sqs = boto3.resource('sqs', region_name=os.environ['REGION'], endpoint_url=os.environ['JOB_QUEUE_URL'])
        self.sqs_queue = self.sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
