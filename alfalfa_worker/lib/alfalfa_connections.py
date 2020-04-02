########################################################################################################################

# -*- coding: utf-8 -*-
from __future__ import print_function

import os

import boto3
from pymongo import MongoClient
from redis import Redis


class AlfalfaConnections:
    """Create connections to data resources for Alfalfa"""

    def __init__(self):
        self.sqs = boto3.resource('sqs', region_name=os.environ['REGION'], endpoint_url=os.environ['JOB_QUEUE_URL'])
        self.queue = self.sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
        self.s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])
        self.redis = Redis(host=os.environ['REDIS_HOST'])
        self.pubsub = self.redis.pubsub()
        self.mongo_client = MongoClient(os.environ['MONGO_URL'])
        self.mongo_db = self.mongo_client[os.environ['MONGO_DB_NAME']]
        self.recs = self.mongo_db.recs
        self.write_arrays = self.mongo_db.writearrays
        self.sims = self.mongo_db.sims
        self.bucket = self.s3.Bucket(os.environ['S3_BUCKET'])
