########################################################################################################################

# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import json
import tarfile

import boto3
from pymongo import MongoClient
from redis import Redis


class AlfalfaConnections:
    """Create connections to data resources for Alfalfa"""

    def __init__(self):
        self.sqs = boto3.resource('sqs', region_name=os.environ['REGION'], endpoint_url=os.environ['JOB_QUEUE_URL'])
        self.queue = self.sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
        self.s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])
        # self.s3_client = boto3.client('s3', os.environ['REGION'])
        self.redis = Redis(host=os.environ['REDIS_HOST'])
        self.pubsub = self.redis.pubsub()
        self.mongo_client = MongoClient(os.environ['MONGO_URL'])
        self.mongo_db = self.mongo_client[os.environ['MONGO_DB_NAME']]
        self.recs = self.mongo_db.recs
        self.write_arrays = self.mongo_db.writearrays
        self.sims = self.mongo_db.sims
        self.bucket = self.s3.Bucket(os.environ['S3_BUCKET'])

    def add_site_to_mongo(self, json_path, site_ref):
        with open(json_path) as json_file:
            data = json.load(json_file)

        # print(data)
        if site_ref:
            array_to_insert = []
            for entity in data:
                array_to_insert.append({
                    '_id': entity['id'].replace('r:', ''),
                    'site_ref': site_ref,
                    'rec': entity
                })
            response = self.recs.insert_many(array_to_insert)
            return response

    def add_site_to_filestore(self, folder_path, site_ref):
        '''
        Purpose: upload the tagged site to the database and cloud
        Inputs: the S3-bucket
        Returns: nothing
        '''
        # get the id of site tag(remove the 'r:')
        if site_ref:
            def reset(tarinfo):
                tarinfo.uid = tarinfo.gid = 0
                tarinfo.uname = tarinfo.gname = "root"

                return tarinfo

            tarname = "%s.tar.gz" % site_ref
            tar = tarfile.open(tarname, "w:gz")
            tar.add(folder_path, filter=reset, arcname=site_ref)
            tar.close()

            upload_location = "parsed/%s" % tarname
            try:
                self.bucket.upload_file(tarname, upload_location)
                return True, upload_location
            except boto3.exceptions.S3UploadFailedError as e:
                return False, e
            except FileNotFoundError as e:
                return False, e
