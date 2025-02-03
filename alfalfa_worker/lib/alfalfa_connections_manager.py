import os

import boto3
from influxdb import InfluxDBClient
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

        # InfluxDB
        self.historian_enabled = os.environ.get('HISTORIAN_ENABLE', False) == 'true'
        if self.historian_enabled:
            self.influx_db_name = os.environ['INFLUXDB_DB']
            self.influx_client = InfluxDBClient(host=os.environ['INFLUXDB_HOST'],
                                                username=os.environ['INFLUXDB_ADMIN_USER'],
                                                password=os.environ['INFLUXDB_ADMIN_PASSWORD'])
        else:
            self.influx_db_name = None
            self.influx_client = None
