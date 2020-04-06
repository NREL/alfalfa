import subprocess
from unittest import TestCase
import pytest
from alfalfa_client import AlfalfaClient
import os


@pytest.mark.integration
class TestSubmitFile(TestCase):
    def setUp(self):
        # Verify that docker is up and running
        r = subprocess.call(['docker', 'ps'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.assertEqual(r, 0)

        # Build and launch an instance of Alfalfa
        self.client = AlfalfaClient(url='http://localhost')

    def test_submit_file(self):
        file = os.path.join(os.path.dirname(__file__), 'SmallOffice_Unitary_1.osm')
        self.assertTrue(os.path.exists(file))
        # It looks like this command hangs...
        site = self.client.submit(file)
        print(site)
        self.assertIsNotNone(site)
