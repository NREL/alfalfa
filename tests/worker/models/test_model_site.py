from unittest import TestCase

from alfalfa_worker.models.sites import Site, session


class TestSiteModel(TestCase):
    def test_create_delete(self):
        """Simple test to make sure we can create and destroy objects through
        the ORM
        """
        objects = [Site(id=0, name='a'), Site(id=1, name='b')]
        session.bulk_save_objects(objects)
        session.commit()
