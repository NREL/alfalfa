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
        id_value = random.randint(0, 1024)
        site = Site(id=id_value, name="test").save()
        updated_at = site.updated_at
        assert site.id == id_value
        assert site.name == "test"
        time.sleep(1)
        site.name = "test_after_update"
        site.save()
        assert site.updated_at > updated_at
        assert site.name == "test_after_update"
        result = site.delete()
        assert result is None

        # try to find the object
        site = Site.objects(id=id_value)
        assert len(site) == 0
