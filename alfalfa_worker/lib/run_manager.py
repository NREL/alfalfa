import os
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from uuid import uuid4

import boto3

from alfalfa_worker.lib.alfalfa_connections_manager import (
    AlafalfaConnectionsManager
)
from alfalfa_worker.lib.enums import SimType
from alfalfa_worker.lib.logger_mixins import LoggerMixinBase
from alfalfa_worker.lib.models import Model, Run, Site


class RunManager(LoggerMixinBase):
    """RunManager is a utility class for handling operations related to runs"""

    def __init__(self, run_dir: os.PathLike):
        super().__init__("RunManager")

        connections_manager = AlafalfaConnectionsManager()

        # Setup S3
        self.s3 = connections_manager.s3
        self.s3_bucket = connections_manager.s3_bucket

        # Redis
        self.redis = connections_manager.redis

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

    def create_model(self, file_path: os.PathLike) -> Model:
        file_path = Path(file_path)
        if file_path.is_dir():
            temp_dir = Path(tempfile.gettempdir())
            file_path = Path(shutil.make_archive(temp_dir / file_path.stem, "zip", file_path))

        model_name = file_path.name
        model = Model(model_name=model_name)
        model.save()

        self.s3_upload(file_path, model.path)

        return model

    def create_run_from_model(self, model_id: str, sim_type=SimType.OPENSTUDIO, run_id=None) -> Run:
        """Create a new Run with the contents of a model"""
        run_id = run_id if run_id is not None else str(uuid4())
        self.logger.info(f"creating from from model with id: {model_id}")
        model: Model = Model.objects.get(ref_id=model_id)
        self.logger.info(model)

        model_name = model.model_name

        file_path = self.tmp_dir / model_name
        run_path = self.run_dir / run_id
        if Path.exists(run_path):
            shutil.rmtree(run_path)
        run_path.mkdir()

        key = "uploads/%s/%s" % (model_id, model_name)
        self.s3_download(key, file_path)
        ext = os.path.splitext(model_name)[1]
        if ext == '.zip':
            zip_file = zipfile.ZipFile(file_path)
            zip_file.extractall(run_path)
            file_path.unlink()
        else:
            shutil.copy(file_path, run_path)
        run = Run(dir=run_path, model=model, ref_id=run_id, sim_type=sim_type, name=model_name)
        run.save()
        # self.register_run(run)
        return run

    def create_empty_run(self) -> Run:
        """Create a new Run with an empty directory"""
        run = Run()
        run_path = self.run_dir / run.ref_id
        run_path.mkdir()
        run.dir = run_path
        run.save()
        return run

    def checkin_run(self, run: Run) -> tuple[bool, str]:
        """Upload Run to s3 and delete local files"""

        run.save()

        def reset(tarinfo):
            tarinfo.uid = tarinfo.gid = 0
            tarinfo.uname = tarinfo.gname = "root"

            return tarinfo

        self.logger.info(f"Checking in run with ID {run.ref_id}")
        # Add an instance of this into the database regardless if
        # it is there or not. This is because the checkin code
        # is called when there are failures, etc., and it breaks
        # the front end when it tries to find the objects.
        Site(ref_id=run.ref_id)
        tarname = "%s.tar.gz" % run.ref_id
        tar_path = self.tmp_dir / tarname
        tar = tarfile.open(tar_path, "w:gz")
        tar.add(run.dir, filter=reset, arcname=run.ref_id)
        tar.close()

        upload_location = "run/%s" % tarname
        try:
            self.logger.info(f"uploading {tarname} to {upload_location}")
            self.s3_upload(tar_path, upload_location)
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

        run = Run.objects.get(ref_id=run_id)
        run.dir = run_path
        return run

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
