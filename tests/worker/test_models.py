# from alfalfa.worker.models import Site

import copy
import os
import random
import time

from mongoengine import connect

# use the mongo test config file
from alfalfa_worker.lib.models import Rec, Run, Site
from alfalfa_worker.lib.run import Run as RunWorker
from alfalfa_worker.lib.sim_type import SimType
from tests.worker.helpers.mock_mongo_data import rec_data, run_data, site_data


class TestModelsObjects:
    def setup(self):
        """Create the connection to the mongodatabase since we are not loading the entire framework.
        Note that the config params are monkeypatched in the conftest file"""
        connect(host=f"{os.environ['MONGO_URL']}/{os.environ['MONGO_DB_NAME']}", uuidrepresentation='standard')

    def test_create_and_destroy_site(self):
        id_value = str(random.randint(0, 1024))
        site = Site(name="test", ref_id=id_value).save()
        updated_at = site.modified
        assert site.ref_id == id_value
        assert site.name == "test"
        time.sleep(1)
        site.name = "test_after_update"
        site.save()
        assert site.modified > updated_at
        assert site.name == "test_after_update"
        result = site.delete()
        assert result is None

        # try to find the object, which should not exist
        site = Site.objects(ref_id=id_value)
        assert len(site) == 0


class TestModelObjectsWithFixtures():

    def setup(self):
        """Create the connection to the mongodatabase since we are not loading the entire framework.
        Note that the config params are monkeypatched in the conftest file"""
        connect(host=f"{os.environ['MONGO_URL']}/{os.environ['MONGO_DB_NAME']}", uuidrepresentation='standard')

        for datum in site_data:
            site = Site(**datum)
            site.save()

        for datum in copy.deepcopy(rec_data):
            # check if there is a key to replace the site_id with the site object
            if datum['site_id']:
                site = Site.objects(ref_id=datum['site_id'])
                datum['site'] = site[0]
            # remove the site_id key since it is not a field in the Site model
            del datum['site_id']
            Rec(**datum).save()

        for datum in copy.deepcopy(run_data):
            if datum['site_id']:
                site = Site.objects(ref_id=datum['site_id'])
                datum['site'] = site[0]
            # remove the site_id key since it is not a field in the Site model
            del datum['site_id']
            Run(**datum).save()

            # TODO: grab the model object from the database and attach

    def teardown(self):
        """Remove all the data that was generated during this test"""
        for datum in site_data:
            site = Site.objects(ref_id=datum['ref_id']).first()
            site.delete()

        # the cascading delete will (should!) delete the recs as well

    def test_relationships(self):
        sites = Site.objects(ref_id__in=['123', '456'])
        assert len(sites) == 2
        assert len(Rec.objects(ref_id__in=['site_456_rec_1', 'site_456_rec_2'])) == 2

        # verify the relationship between the site and the rec
        site = Site.objects()[1]
        assert site.ref_id == '456'
        assert site.recs().count() == 2
        rec_1 = site.recs()[0]
        assert rec_1.ref_id == 'site_456_rec_1'

    def test_site_rec_querying(self):
        # Based on the mock data, this is the object with 2 recs
        site = Site.objects()[1]
        recs = site.recs(rec__damper='s:disabled')
        assert len(recs) == 1

        recs = site.recs(rec__damper='s:enabled')
        assert len(recs) == 0

    def test_model_to_dict(self):
        run_obj = Run.objects.get(ref_id='run_id_123')

        run = RunWorker(**run_obj.to_dict())
        assert run.sim_type == SimType.OPENSTUDIO
        assert run.created == run_obj.created
