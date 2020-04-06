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
        self.redis = Redis(host=os.environ['REDIS_HOST'])
        self.pubsub = self.redis.pubsub()
        self.mongo_client = MongoClient(os.environ['MONGO_URL'])
        self.mongo_db = self.mongo_client[os.environ['MONGO_DB_NAME']]
        self.recs = self.mongo_db.recs
        self.write_arrays = self.mongo_db.writearrays
        self.sims = self.mongo_db.sims
        self.bucket = self.s3.Bucket(os.environ['S3_BUCKET'])

    def upload_site_to_filestore(self, json_path, folder_path):
        '''
        Purpose: upload the tagged site to the database and cloud
        Inputs: the S3-bucket
        Returns: nothing
        '''
        # get the id of site tag(remove the 'r:')
        site_ref = ''
        with open(json_path) as json_file:
            data = json.load(json_file)
            for entity in data:
                if 'site' in entity:
                    if entity['site'] == 'm:':
                        site_ref = entity['id'].replace('r:', '')
                        break

        if site_ref:
            array_to_insert = []
            for entity in data:
                array_to_insert.append({
                    '_id': entity['id'].replace('r:', ''),
                    'site_ref': site_ref,
                    'rec': entity
                })
            self.recs.insert_many(array_to_insert)
            print("past insert!")
            # print(result)

            def reset(tarinfo):
                tarinfo.uid = tarinfo.gid = 0
                tarinfo.uname = tarinfo.gname = "root"

                return tarinfo

            tarname = "%s.tar.gz" % site_ref
            tar = tarfile.open(tarname, "w:gz")
            tar.add(folder_path, filter=reset, arcname=site_ref)
            tar.close()

            # This upload the tagged site to the cloud
            self.bucket.upload_file(tarname, "parsed/%s" % tarname)
