import datetime
import os
import tarfile
import zipfile
from typing import List

import boto3
import pytz

from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
from alfalfa_worker.lib.logger_mixins import RunManagerLoggerMixin
from alfalfa_worker.lib.point import Point
from alfalfa_worker.lib.run import Run


class RunManager(RunManagerLoggerMixin, AlfalfaConnectionsBase):
    def create_run_from_model(self, upload_id: str, model_name: str, dir_path: str) -> Run:
        zip_file_path = os.path.join(dir_path, "../in.zip")
        key = "uploads/%s/%s" % (upload_id, model_name)
        self.s3_bucket.download_file(key, zip_file_path)
        zip_file = zipfile.ZipFile(zip_file_path)
        zip_file.extractall(dir_path)
        os.remove(zip_file_path)
        run = Run(dir_path, upload_id)
        # TODO register run and give unique id from model_id
        return run

    def checkin_run(self, run: Run):
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
            return True, upload_location
        except boto3.exceptions.S3UploadFailedError as e:
            return False, e
        except FileNotFoundError as e:
            return False, e

    def checkout_run(self, run_id: str, dir_path: str):
        tar_file_path = os.path.join(dir_path, "../in.tar.gz")
        key = f'run/{run_id}.tar.gz'
        self.logger.info(f"downloading {tar_file_path} from {key}")
        self.s3_bucket.download_file(key, tar_file_path)

        tar = tarfile.open(tar_file_path)
        tar.extractall(dir_path)
        tar.close()
        os.remove(tar_file_path)
        return Run(os.path.join(dir_path, run_id), run_id)

    def set_run_status(self, run: Run, status: str):
        self.mongo_db_sims.update_one({'_id': run.id},
                                      {"$set": {"simStatus": status}},
                                      False)

    def complete_run(self, run: Run):
        self.checkin_run(run)
        time = str(datetime.now(tz=pytz.UTC))
        self.mongo_db_sims.update_one({"_id": run.id},
                                      {"$set": {"simStatus": "Complete", "timeCompleted": time, "s3Key": f"run/{run.id}"}},
                                      False)

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
