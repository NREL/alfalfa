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
from alfalfa_worker.lib.models import Model, Rec, RecInstance, Run, Site


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
        run = Run(dir=run_path, model=model, ref_id=run_id, sim_type=sim_type)
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

    def checkin_run(self, run: Run):
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

    def add_site_to_mongo(self, haystack_json: dict, run: Run):
        """Upload JSON documents to mongo.  The documents look as follows:
        {
            '_id': '...', # this maps to the 'id' below, the unique id of the entity record.
            'rec': {
                'id': '...',
                'siteRef': '...'
                ...other Haystack tags for rec
            }
        }
        :param haystack_json: json Haystack document
        :param run: id of the run
        :return: None
        """
        # Create a site obj here to keep the variable active, but it is
        # really set as index 0 of the haystack_json
        site = None

        # create all of the recs for this site
        for index, entity in enumerate(haystack_json):
            id = entity['id'].replace('r:', '')

            # Create default writearray objects for the site. Create this on the backend
            # to ensure that the links are created correctly and accessible from the frontend.
            #   Only check for records tagged with writable.
            #   This may need to be expanded to other types in the future.
            cur_status = entity.pop('curStatus', None)
            cur_val = entity.pop('curVal', None)
            if entity.get('writable') == 'm:':
                mapping = {}
                if cur_status is not None:
                    mapping['curStatus'] = cur_status
                if cur_val is not None:
                    mapping['curVal'] = cur_val
                if mapping:
                    # Note that run.ref_id is currently the same as site.ref_id, but
                    # this won't be the case in the future.
                    self.redis.hset(f'site:{run.ref_id}:rec:{id}', mapping=mapping)

            if index == 0:
                # this is the site record, store it on the site object of the
                # database (as well as in the recs collection, for now).
                # TODO: convert to actual data types (which requires updating the mongo schema too)
                # TODO: FMU's might not have this data?
                name = f"{entity.get('dis', 'Test Case').replace('s:','')} in {entity.get('geoCity', 'Unknown City').replace('s:','')}"
                # there might be the case where the ref_id was added to the record during
                # a "checkin" but the rest of that is not know. So get or create the Site.
                site = Site(ref_id=run.ref_id)
                site.name = name
                site.haystack_raw = haystack_json
                site.dis = entity.get('dis')
                site.site = entity.get('site')
                site.area = entity.get('area')
                site.weather_ref = entity.get('weatherRef')
                site.tz = entity.get('tz')
                site.geo_city = entity.get('geoCity')
                site.geo_state = entity.get('geoState')
                site.geo_country = entity.get('geoCountry')
                site.geo_coord = entity.get('geoCoord')
                site.sim_status = entity.get('simStatus')
                site.sim_type = entity.get('simType')
                site.save()

            rec = Rec(ref_id=id, site=site).save()
            rec_instance = RecInstance(**entity)
            rec.rec = rec_instance
            rec.save()

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
