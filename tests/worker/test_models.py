# from alfalfa.worker.models import Site

import time
from unittest import TestCase

# use the mongo test config file
from alfalfa_worker.lib.models import Site


class TestModelAdvancerBase(TestCase):
    """The mongo database connection occures in the alfalfa_connections_base.py file, so you don't
    need to explicity connect to the database in this file."""

    def test_create_and_destroy_site(self):
        site = Site(id=1, name="test").save()
        updated_at = site.updated_at
        assert site.id == 1
        assert site.name == "test"
        time.sleep(1)
        site.name = "test_after_update"
        site.save()
        assert site.updated_at > updated_at
        result = site.delete()
        assert result is None
