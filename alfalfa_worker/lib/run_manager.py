import os
import tarfile
import zipfile
from typing import List

import boto3
from pymongo import MongoClient

from alfalfa_worker.lib.logger_mixins import LoggerMixinBase
from alfalfa_worker.lib.point import Point
from alfalfa_worker.lib.run import Run, RunStatus


class RunManager(LoggerMixinBase):
    def __init__(self):
        super().__init__("RunManager")
        # Setup S3
        self.s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])
        self.s3_bucket = self.s3.Bucket(os.environ['S3_BUCKET'])

        # Setup Mongo
        self.mongo_client = MongoClient(os.environ['MONGO_URL'])
        self.mongo_db = self.mongo_client[os.environ['MONGO_DB_NAME']]
        self.mongo_db_runs = self.mongo_db.runs
        self.mongo_db_recs = self.mongo_db.recs
        self.mongo_db_sims = self.mongo_db.sims

    def create_run_from_model(self, upload_id: str, model_name: str, dir_path: str) -> Run:
        file_path = os.path.join(dir_path, model_name)
        key = "uploads/%s/%s" % (upload_id, model_name)
        self.s3_bucket.download_file(key, file_path)
        ext = os.path.splitext(model_name)[1]
        if ext == '.zip':
            zip_file = zipfile.ZipFile(file_path)
            zip_file.extractall(dir_path)
            os.remove(file_path)
        run = Run(dir_path, key, upload_id)
        self.register_run(run)
        # TODO register run and give unique id from model_id
        return run

    def register_run(self, run: Run):
        run_dict = run.to_dict()
        self.mongo_db_runs.insert_one(run_dict)

    def update_db(self, run: Run):
        self.mongo_db_runs.update_one({'_id': run.id},
                                      {'$set': run.to_dict()}, False)
        self.logger.info(run.status)
        self.mongo_db_recs.update_one({'_id': run.id},
                                      {'$set': {'simStatus': run.status.value}}, False)

    def checkin_run(self, run: Run):
        run.status = RunStatus.COMPLETE

        def reset(tarinfo):
            tarinfo.uid = tarinfo.gid = 0
            tarinfo.uname = tarinfo.gname = "root"

            return tarinfo

        tarname = "%s.tar.gz" % run.id
        tar = tarfile.open(tarname, "w:gz")
        tar.add(run.dir, filter=reset, arcname=run.id)
        tar.close()

        upload_location = "run/%s" % tarname
        try:
            self.logger.info(f"uploading {tarname} to {upload_location}")
            self.s3_bucket.upload_file(tarname, upload_location)
            self.update_db(run)
            return True, upload_location
        except boto3.exceptions.S3UploadFailedError as e:
            return False, e
        except FileNotFoundError as e:
            return False, e

    def checkout_run(self, run_id: str, dir_path: str) -> Run:
        tar_file_path = os.path.join(dir_path, "../in.tar.gz")
        key = f'run/{run_id}.tar.gz'
        self.logger.info(f"downloading {tar_file_path} from {key}")
        self.s3_bucket.download_file(key, tar_file_path)

        tar = tarfile.open(tar_file_path)
        tar.extractall(dir_path)
        tar.close()
        os.remove(tar_file_path)

        run_dict = self.mongo_db_runs.find_one({'_id': run_id})
        self.logger.info(run_dict)
        run = Run(os.path.join(dir_path, run_id), **run_dict)
        run.status = RunStatus.STARTING
        self.update_db(run)
        return run

    def add_points(self, run: Run, points: List[Point]):
        array_to_insert = []
        for point in points:
            array_to_insert.append({
                '_id': point.id,
                'site_ref': run.id,
                'type': point.type.name,
                'rec': point.rec
            })

        response = self.mongo_db_recs.insert_many(array_to_insert)
        return response

    def add_site_to_mongo(self, haystack_json, run: Run):
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
        array_to_insert = []
        for entity in haystack_json:
            array_to_insert.append({
                '_id': entity['id'].replace('r:', ''),
                'site_ref': run.id,
                'rec': entity
            })
        response = self.mongo_db_recs.insert_many(array_to_insert)
        return response
