import json
import os
from subprocess import call
from unittest import TestCase

import pytest


@pytest.mark.fmu
class TestAddSiteFmu(TestCase):
    def test_fmu_create_tags(self):
        # test creating FMU tags
        output_path = 'tests/worker/add_site/output'
        os.makedirs(output_path, exist_ok=True)

        py_file = 'alfalfa_worker/lib/fmu_create_tags.py'
        fmu_path = os.path.join('tests/integration/models/simple_1_zone_heating.fmu')
        fmu_filename = 'simple_1_zone_heating.fmu'
        fmu_json = f'{output_path}/tags.json'
        if os.path.exists(fmu_json):
            os.remove(fmu_json)

        # TODO: Need to run this with Python3, eventually
        # Better yet, convert the fmu_create_tags.py into a class.
        r = call(['python3', py_file, fmu_path, fmu_filename, fmu_json])

        assert r == 0, "fmu_create_tags failed to successfully run"
        assert os.path.exists(fmu_json)

        # verify that the resulting file is JSON and content
        tags = json.load(open(fmu_json))
        assert len(tags) == 4
        assert tags[0]['dis'] == 's:simple_1_zone_heating'
