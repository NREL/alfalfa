import subprocess
from unittest import TestCase
import pytest
import os
import time

# Local imports
from alfalfa_client import AlfalfaClient
from alfalfa_worker.lib.alfalfa_connections import AlfalfaConnections


@pytest.mark.integration
class TestSubmitFile(TestCase):
    """
    Tests three things for each potential upload file type (osm, zip, fmu):
    1. AlfalfaClient returns an ID for a site
    2. The site exists in MongoDB
    3. The site exists in the filestore (s3 bucket)
    :return:
    """

    def setUp(self):
        # Verify that docker is up and running
        r = subprocess.call(['docker', 'ps'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.assertEqual(r, 0)

        # Connect to Alfalfa and other services
        self.client = AlfalfaClient(url='http://localhost')
        self.ac = AlfalfaConnections()

        # For reuse
        self.files_dir = os.path.join(os.path.dirname(__file__), 'files')
        self.osm_file_name = 'SmallOffice_Unitary_1.osm'
        self.osw_file_name = 'OSWTestForAlfalfa20200323-002.zip'
        self.fmu_file_name = 'simple_1_zone_heating.fmu'

    def test_submit_osm(self):
        f = os.path.join(self.files_dir, self.osm_file_name)
        self.check_file_exists(f)
        self.check_mongo_response('.osm')
        self.check_filestore(self.osm_file_name)

    def test_submit_osw_as_zip(self):
        f = os.path.join(self.files_dir, self.osw_file_name)
        self.check_file_exists(f)
        self.check_mongo_response('.zip')
        self.check_filestore(self.osw_file_name)

    def test_submit_fmu(self):
        f = os.path.join(self.files_dir, self.fmu_file_name)
        self.check_file_exists(f)
        self.check_mongo_response('.fmu')
        self.check_filestore(self.fmu_file_name)

    def check_file_exists(self, f):
        """
        Test 1 - ensure client returns a site_id

        :param f: file to submit to Alfalfa
        """
        self.assertTrue(os.path.exists(f))
        self.site_id = self.client.submit(f)
        self.assertIsNotNone(self.site_id)

    def check_mongo_response(self, ext):
        """
        Test 2 - Check the site rec exists in Mongo.
        The '_id' attribute in Mongo
        should be the same as the entity id - therefore, the find_one
        should return us the site record

        :param ext: '.osm', '.zip', '.fmu'
        :return:
        """
        if ext == '.fmu':
            sim_type = 's:fmu'
        else:
            sim_type = 's:osm'
        mongo_response = self.ac.mongo_db_recs.find_one({'_id': self.site_id})
        self.assertIsNotNone(mongo_response)
        self.assertIsNotNone(mongo_response.get('rec', None))
        rec = mongo_response['rec']
        self.assertEqual(rec.get('site', None), "m:")
        self.assertEqual(rec.get('simType', None), sim_type)
        self.assertEqual(rec.get('simStatus', None), 's:Stopped')

    def check_filestore(self, f):
        """
        Test3 - Check site is in both uploads/ and parsed/ on filestore

        :param f: name of file
        :return:
        """
        # this was intermittently failing, seemed to be timing issue
        time.sleep(5)
        objs = []
        all_objs = None
        all_objs = self.ac.s3_bucket.objects.all()
        self.assertIsNotNone(all_objs)
        for obj in all_objs:
            objs.append(obj.key)
        upload_path = "uploads/{}/{}".format(self.site_id, f)
        parsed_path = "parsed/{}.tar.gz".format(self.site_id)
        self.assertTrue(upload_path in objs)
        self.assertTrue(parsed_path in objs)
