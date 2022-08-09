# from alfalfa.worker.models import Site

import os
import random
import time

from mongoengine import connect

# use the mongo test config file
from alfalfa_worker.lib.models import Site


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
