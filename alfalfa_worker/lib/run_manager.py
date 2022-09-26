import os
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import List
from uuid import uuid4

import boto3
from pymongo import MongoClient
from redis import Redis

from alfalfa_worker.lib.logger_mixins import LoggerMixinBase
from alfalfa_worker.lib.point import Point, PointType
from alfalfa_worker.lib.run import Run
from alfalfa_worker.lib.sim_type import SimType


class RunManager(LoggerMixinBase):
    """RunManager is a utility class for handling operations related to runs"""

    def __init__(self, run_dir: os.PathLike):
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
        self.mongo_db_points = self.mongo_db.points

        # Setup Redis
        self.redis = Redis(host=os.environ['REDIS_HOST'])

        self.run_dir = Path(run_dir)
        self.tmp_dir = self.run_dir / 'tmp'
        if not Path.exists(self.tmp_dir):
            self.tmp_dir.mkdir()

    def s3_download(self, key: str, file_path: os.PathLike):
        """Download a file from s3"""
        self.s3_bucket.download_file(key, str(file_path))

    def s3_upload(self, file_path: os.PathLike, key: str):
        """Upload a file to s3"""
        self.s3_bucket.upload_file(str(file_path), key)

    def create_run_from_model(self, upload_id: str, model_name: str, sim_type=SimType.OPENSTUDIO) -> Run:
        """Create a new Run with the contents of a model"""
        file_path = self.tmp_dir / model_name
        run_path = self.run_dir / upload_id
        if Path.exists(run_path):
            shutil.rmtree(run_path)
        run_path.mkdir()

        key = "uploads/%s/%s" % (upload_id, model_name)
        self.s3_download(key, file_path)
        ext = os.path.splitext(model_name)[1]
        if ext == '.zip':
            zip_file = zipfile.ZipFile(file_path)
            zip_file.extractall(run_path)
            file_path.unlink()
        else:
            shutil.copy(file_path, run_path)
        run = Run(dir=run_path, model=key, _id=upload_id, sim_type=sim_type)
        self.register_run(run)
        return run

    def create_empty_run(self) -> Run:
        """Create a new Run with an empty directory"""
        run = Run()
        run_path = self.run_dir / run.id
        run_path.mkdir()
        run.dir = run_path
        self.register_run(run)
        return run

    def checkin_run(self, run: Run):
        """Upload Run to s3 and delete local files"""

        def reset(tarinfo):
            tarinfo.uid = tarinfo.gid = 0
            tarinfo.uname = tarinfo.gname = "root"

            return tarinfo

        tarname = "%s.tar.gz" % run.id
        tar_path = self.tmp_dir / tarname
        tar = tarfile.open(tar_path, "w:gz")
        tar.add(run.dir, filter=reset, arcname=run.id)
        tar.close()

        upload_location = "run/%s" % tarname
        try:
            self.logger.info(f"uploading {tarname} to {upload_location}")
            self.s3_upload(tar_path, upload_location)
            self.update_db(run)
            os.remove(tar_path)
            shutil.rmtree(run.dir)
            return True, upload_location
        except boto3.exceptions.S3UploadFailedError as e:
            return False, e
        except FileNotFoundError as e:
            return False, e

    def checkout_run(self, run_id: str) -> Run:
        """Download Run contents and create Run object"""
        tar_file_path = self.tmp_dir / f"{run_id}.tar.gz"
        run_path = self.run_dir / run_id
        key = f'run/{run_id}.tar.gz'
        self.logger.info(f"downloading {tar_file_path} from {key}")
        self.s3_download(key, tar_file_path)

        tar = tarfile.open(tar_file_path)
        tar.extractall(self.run_dir)
        tar.close()
        os.remove(tar_file_path)

        run = self.get_run(run_id)
        run.dir = run_path
        return run

    def register_run(self, run: Run):
        """Insert a new run into mongo"""
        run_dict = run.to_dict()
        self.mongo_db_runs.insert_one(run_dict)

    def update_db(self, run: Run):
        """Update Run object and associated points in mongo. Writes output points and reads input points"""
        # If we used some sort of ORM we could possibly just have db objects which sync themselves automagically
        self.mongo_db_runs.update_one({'_id': run.id},
                                      {'$set': run.to_dict()}, False)
        for point in run.points:
            if point.type == PointType.OUTPUT and point._pending_value:
                self.mongo_db_points.update_one({'_id': point.id},
                                                {'$set': {'val': point.val}}, False)
            else:
                point_dict = self.mongo_db_points.find_one({'_id': point.id})
                point._val = point_dict['val']

    def get_run(self, run_id: str) -> Run:
        """Get a run by id from the database"""
        run_dict = self.mongo_db_runs.find_one({'_id': run_id})
        self.logger.info(run_dict)
        run = Run(**run_dict)
        run.points = self.get_points(run)
        return run

    def get_points(self, run: Run):
        """Get a list of all points that exist in a run"""
        points_res = self.mongo_db_points.find({'run_id': run.id})
        points: List[Point] = []
        for point_dict in points_res:
            point_dict['id'] = point_dict['_id']
            del point_dict['_id']
            del point_dict['run_id']
            points.append(Point(**point_dict))
        return points

    def add_points_to_run(self, run: Run, points: List[Point]):
        """Add a list of points to a Run"""
        array_to_insert = []
        for point in points:
            point_dict = {
                '_id': point.id,
                'key': point.key,
                'name': point.name,
                'run_id': run.id,
                'val': point.val
            }
            array_to_insert.append(point_dict)

        response = self.mongo_db_points.insert_many(array_to_insert)
        run.points = points
        return response

    # TODO deprecate
    def add_site_to_db(self, haystack_json, run: Run):
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
            _id = entity['id'].replace('r:', '')

            curStatus = entity.pop('curStatus', None)
            curVal = entity.pop('curVal', None)
            mapping = {}
            if curStatus is not None:
                mapping['curStatus'] = curStatus
            if curVal is not None:
                mapping['curVal'] = curVal
            if mapping:
                self.redis.hset(f'site:{run.id}:rec:{_id}', mapping=mapping)

            array_to_insert.append({
                '_id': _id,
                'site_ref': run.id,
                'rec': entity
            })
        response = self.mongo_db_recs.insert_many(array_to_insert)
        return response

    def add_model(self, model_path: os.PathLike):
        upload_id = str(uuid4())
        model_path = Path(model_path)
        upload_path = Path('uploads') / upload_id
        if model_path.is_dir():
            archive_name = model_path.name + '.zip'
            upload_path = upload_path / archive_name
            archive_path = shutil.make_archive(archive_name, 'zip', model_path)
            self.s3_upload(archive_path, str(upload_path))
        else:
            upload_path = upload_path / model_path.name
            self.s3_upload(model_path, str(upload_path))

        return upload_id, upload_path.name
