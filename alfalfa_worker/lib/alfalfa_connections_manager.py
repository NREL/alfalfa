import os
import time
import logging

import boto3
from influxdb import InfluxDBClient
from mongoengine import connect
from redis import Redis

from alfalfa_worker.lib.singleton import Singleton


class AlafalfaConnectionsManager(metaclass=Singleton):

    def __init__(self) -> None:
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize connections incrementally
        self._setup_s3_connection()
        self._setup_mongo_connection()
        self._setup_redis_connection()
        self._setup_influx_connection()

    def _wait_for_service(self, service_name, check_function, max_retries=30, retry_delay=2):
        """
        Wait for a service to become available with fixed retry delay
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Attempting to connect to {service_name} (attempt {attempt + 1}/{max_retries})")
                if check_function():
                    self.logger.info(f"Successfully connected to {service_name}")
                    return True
            except Exception as e:
                self.logger.warning(f"Failed to connect to {service_name}: {e}")
            
            if attempt < max_retries - 1:
                self.logger.info(f"Waiting {retry_delay} seconds before retrying {service_name}")
                time.sleep(retry_delay)
        
        raise ConnectionError(f"Failed to connect to {service_name} after {max_retries} attempts")

    def _setup_s3_connection(self):
        """Setup S3/MinIO connection with retry logic"""
        def check_s3():
            self.s3 = boto3.resource('s3', region_name=os.environ['S3_REGION'], endpoint_url=os.environ['S3_URL'])
            self.s3_bucket = self.s3.Bucket(os.environ['S3_BUCKET'])
            # Test the connection by listing buckets
            list(self.s3.buckets.all())
            return True
        
        self._wait_for_service("S3/MinIO", check_s3)

    def _setup_mongo_connection(self):
        """Setup MongoDB connection with retry logic"""
        def check_mongo():
            # Get the MongoDB connection string from environment
            mongo_url = os.environ['MONGO_URL']
            self.logger.info(f"Using MONGO_URL: {mongo_url}")
            
            # Connect using the connection string
            connect(host=mongo_url, uuidrepresentation='standard', serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
            
            # Test the connection
            from mongoengine import connection
            db = connection.get_db()
            db.command('ping')
            return True
        
        self._wait_for_service("MongoDB", check_mongo)

    def _setup_redis_connection(self):
        """Setup Redis connection with retry logic"""
        def check_redis():
            # Get the Redis connection string from environment
            redis_url = os.environ['REDIS_URL']
            self.logger.info(f"Using REDIS_URL: {redis_url}")
            
            # Connect using the connection string
            self.redis = Redis.from_url(redis_url)
            # Test the connection
            self.redis.ping()
            return True
        
        self._wait_for_service("Redis", check_redis)

    def _setup_influx_connection(self):
        """Setup InfluxDB connection with retry logic"""
        # InfluxDB
        self.historian_enabled = os.environ.get('HISTORIAN_ENABLE', False) == 'true'
        if self.historian_enabled:
            def check_influx():
                self.influx_db_name = os.environ['INFLUXDB_DB']
                self.influx_client = InfluxDBClient(host=os.environ['INFLUXDB_HOST'],
                                                    username=os.environ['INFLUXDB_USERNAME'],
                                                    password=os.environ['INFLUXDB_PASSWORD'])
                # Test the connection
                self.influx_client.ping()
                return True
            
            self._wait_for_service("InfluxDB", check_influx)
        else:
            self.influx_db_name = None
            self.influx_client = None
            self.logger.info("InfluxDB historian is disabled")
