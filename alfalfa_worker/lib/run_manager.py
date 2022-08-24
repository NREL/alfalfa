import os
import shutil
import tarfile
import zipfile
from pathlib import Path
from typing import List
from uuid import uuid4

import boto3
from mongoengine import connect

from alfalfa_worker.lib.logger_mixins import LoggerMixinBase
from alfalfa_worker.lib.models import Model
from alfalfa_worker.lib.models import Point as PointMongo
from alfalfa_worker.lib.models import Rec, RecInstance
from alfalfa_worker.lib.models import Run as RunMongo
from alfalfa_worker.lib.models import Site
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

        # Mongo - connect using mongoengine
        connect(host=f"{os.environ['MONGO_URL']}/{os.environ['MONGO_DB_NAME']}", uuidrepresentation='standard')

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

        # configure the data for the new database format
        run_dict['ref_id'] = run_dict.pop('_id')

        # remove sim_time since it is None, which isn't valid in the database, so leave empty and
        # it will not be in the database, yet.
        run_dict.pop('sim_time')

        # grab the model to assign it to the relationship later
        model_path = run_dict.pop('model')
        model = Model(path=model_path).save()

        # create site relationship - which is really the run.id, for some reason
        try:
            site = Site.objects.get(ref_id=run.id)
            run_dict['site'] = site
        except Site.DoesNotExist:
            # this must be the first time this object is being created, so there is no site yet
            # since the site is extracted from the haystack points
            pass

        # create the Run database object - this is the initial creation of it.
        run_obj = RunMongo(**run_dict).save()
        # set the database object references
        run_obj.model = model
        run_obj.save()

    def update_db(self, run: Run):
        """Update Run object and associated points in mongo. Writes output points and reads input points"""
        run_dict = run.to_dict()
        self.logger.info(f"HERERREE updating {run_dict}")

        # update in the mongo ORM, which requires a bit of massaging. The run update should only care about:
        #    * job_history
        #    * status
        #    * modified (which is implicit)
        #    * sim_time
        #    * error_log
        new_obj = {
            'job_history': run_dict['job_history'],
            'status': run_dict['status'],
            'sim_time': run_dict['sim_time'],
            'error_log': run_dict['error_log'],
        }
        # check if the site is assigned yet and create site relationship -
        # which is really the run.id, for some reason
        try:
            site = Site.objects.get(ref_id=run.id)
            new_obj['site'] = site
        except Site.DoesNotExist:
            # this must be the first time this object is being created, so there is no site yet
            # since the site is extracted from the haystack points
            pass

        RunMongo.objects(ref_id=run.id).update_one(**new_obj)
        for point in run.points:
            if point.type == PointType.OUTPUT and point._pending_value:
                PointMongo.objects.get(ref_id=point.id).update(value=point.val)
            else:
                # set the current point in memory to the value in the database (since it is an input)
                point_obj = PointMongo.objects.get(ref_id=point.id)
                # and in the new database model
                point._val = point_obj.value

    def get_run(self, run_id: str) -> Run:
        """Get a run by id from the database"""
        # Use the new model -- find, but don't set
        run_obj = RunMongo.objects.get(ref_id=run_id)
        self.logger.info(f"Retrieved run object from the database {run_obj}")

        # TODO: the Run object should already be a db object, update this
        run = Run(**run_obj.to_dict())
        run.points = self.get_points(run)

        # why are we setting this time?
        run.sim_time = run_obj.sim_time

        return run

    def get_points(self, run: Run):
        """Get a list of all points that exist in a run"""
        # Use the new model -- find in the new database format, but don't set anything yet.
        points_res = PointMongo.objects(ref_id=run.id)
        points: List[Point] = []
        for point_dict in points_res:
            # create a list of dicts for the Point object on the Run.
            # However, the point object should be database aware, fix this.
            point_dict = point_dict.to_dict()
            point_dict['id'] = point_dict['_id']
            del point_dict['_id']
            del point_dict['run_id']
            points.append(Point(**point_dict))

        return points

    def add_points_to_run(self, run: Run, points: List[Point]):
        """Add a list of points to a Run"""

        # TODO: this should be cleaned up a bit more. Lots of work to make this happen
        array_to_insert = []
        for point in points:
            array_to_insert.append({
                '_id': point.id,
                'key': point.key,
                'name': point.name,
                'run_id': run.id,
                'val': point.val
            })

        # store into the new database format, load_bulk=False only returns obj ids.
        #   - need to massage the data a bit, mark ref_id and run_id as object.
        run_id_obj = RunMongo.objects.filter(ref_id=run.id).first()
        new_points = []
        for index, _point in enumerate(array_to_insert):
            array_to_insert[index]['ref_id'] = array_to_insert[index].pop('_id')
            array_to_insert[index]['run'] = run_id_obj  # need to add the db object reference
            del array_to_insert[index]['run_id']
            array_to_insert[index]['value'] = array_to_insert[index].pop('val')  # let's rename to a fuller description
            new_points.append(PointMongo(**array_to_insert[index]))
        response = PointMongo.objects.insert(new_points, load_bulk=True)

        # Why are the run.points being assigned here?
        run.points = points

        return response

    def add_site_to_mongo(self, haystack_json: dict, run: Run):
        """Upload JSON documents to mongo.  The documents look as follows:
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
        :return: None
        """
        # Create a site obj here to keep the variable active, but it is
        # really set as index 0 of the haystack_json
        site = None

        # create all of the recs for this site
        for index, entity in enumerate(haystack_json):
            if index == 0:
                # this is the site record, store it on the site object of the
                # database (as well as in the recs collection, for now).
                # TODO: convert to actual data types (which requires updating the mongo schema too)
                # TODO: FMU's might not have this data?
                name = f"{entity.get('dis','Test Case').replace('s:','')} in {entity.get('geoCity', 'Unknown City').replace('s:','')}"
                site = Site(ref_id=run.id, name=name).save()
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

            rec = Rec(ref_id=entity['id'].replace('r:', ''), site=site).save()

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
