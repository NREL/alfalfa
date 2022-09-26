########################################################################################################################

# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import tarfile

import boto3
from influxdb import InfluxDBClient
from pymongo import MongoClient
from redis import Redis


class AlfalfaConnectionsBase(object):
    """Create connections to data resources for Alfalfa"""

    def __init__(self):
        """
        boto3 is the AWS SDK for Python for different types of services (S3, EC2, etc.)
        """
        # boto3
        self.sqs = boto3.resource('sqs', region_name=os.environ['REGION'], endpoint_url=os.environ['JOB_QUEUE_URL'])
        self.sqs_queue = self.sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
        self.s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])
        self.s3_bucket = self.s3.Bucket(os.environ['S3_BUCKET'])

        # Redis
        self.redis = Redis(host=os.environ['REDIS_HOST'])
        self.redis_pubsub = self.redis.pubsub()

        # Mongo
        self.mongo_client = MongoClient(os.environ['MONGO_URL'])
        self.mongo_db = self.mongo_client[os.environ['MONGO_DB_NAME']]
        self.mongo_db_recs = self.mongo_db.recs
        self.mongo_db_sims = self.mongo_db.sims

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

    def add_site_to_db(self, haystack_json, site_ref):
        """
        Upload JSON documents to mongo.  The documents look as follows:
        {
            '_id': '...', # this maps to the 'id' below, the unique id of the entity record.
            'site_ref': '...', # for easy finding of entities by site
            'rec': {
                'id': '...',
                'siteRef': '...'
                ...other Haystack tags for rec
            }
        }
        :param haystack_json: json Haystack document
        :param site_ref: id of site
        :return: pymongo.results.InsertManyResult
        """
        if site_ref:
            array_to_insert = []
            for entity in haystack_json:
                _id = entity['id'].replace('r:', '')

                curStatus = entity.pop('curStatus', None)
                curVal = entity.pop('curVal', None)
                mapping = {}
                if curStatus is not None:
                    mapping['curStatus'] = curStatus
                if curVal is not None:
                    mapping['curVal'] = curVal
                if mapping:
                    self.redis.hset(f'site:{site_ref}:rec:{_id}', mapping=mapping)

                array_to_insert.append({
                    '_id': _id,
                    'site_ref': site_ref,
                    'rec': entity
                })
            response = self.mongo_db_recs.insert_many(array_to_insert)
            return response

    def add_site_to_filestore(self, bucket_parsed_site_id_dir, site_ref):
        """
        Attempt to add to filestore.  Two exceptions are caught and returned back:
        1. S3 upload error
        2. File not found error
        :param bucket_parsed_site_id_dir: directory to upload to on s3 bucket after parsing: parsed/{site_id}/.
        :param site_ref: id of site
        :return: one of two options:
            1. True, parsed tarball upload location
            2. False, error thrown
        """
        # get the id of site tag(remove the 'r:')
        if site_ref:
            def reset(tarinfo):
                tarinfo.uid = tarinfo.gid = 0
                tarinfo.uname = tarinfo.gname = "root"

                return tarinfo

            tarname = "%s.tar.gz" % site_ref
            tar = tarfile.open(tarname, "w:gz")
            tar.add(bucket_parsed_site_id_dir, filter=reset, arcname=site_ref)
            tar.close()

            upload_location = "parsed/%s" % tarname
            try:
                self.s3_bucket.upload_file(tarname, upload_location)
                return True, upload_location
            except boto3.exceptions.S3UploadFailedError as e:
                return False, e
            except FileNotFoundError as e:
                return False, e
