import datetime

from mongoengine import (
    DateTimeField,
    DictField,
    Document,
    DynamicField,
    EmbeddedDocument,
    EmbeddedDocumentField,
    FloatField,
    IntField,
    ListField,
    ReferenceField,
    StringField,
    UUIDField
)

from alfalfa_worker.lib.sim_type import SimType


class TimestampedDocument(Document):
    """Create a class to save the created_at and updated_at fields automatically"""
    meta = {'allow_inheritance': True, 'abstract': True}

    created = DateTimeField(required=True, default=datetime.datetime.now)
    modified = DateTimeField(required=True, default=datetime.datetime.now)

    def save(self, force_insert=False, validate=True, clean=True, write_concern=None, cascade=None,
             cascade_kwargs=None, _refs=None, save_condition=None, signal_kwargs=None, **kwargs,):
        self.modified = datetime.datetime.now()
        return super().save(
            force_insert, validate, clean, write_concern, cascade, cascade_kwargs, _refs, save_condition,
            signal_kwargs, **kwargs
        )


class Site(TimestampedDocument):
    meta = {'collection': 'site'}

    # external reference ID
    ref_id = StringField(required=True, index=True, primary_key=True)
    name = StringField(required=True, max_length=255)
    haystack = DictField()


class RecInstance(EmbeddedDocument):
    """This is a flat haystack representation of a point"""

    id = StringField(primary_key=True)
    dis = StringField()
    siteRef = StringField()
    point = StringField()
    cur = StringField()
    curVal = StringField()
    curStatus = StringField()
    kind = StringField()
    site = StringField()
    simStatus = StringField()
    datetime = StringField()
    simType = StringField()
    writable = StringField()
    writeStatus = StringField()
    area = StringField()
    geoCoord = StringField()
    geoCountry = StringField()
    geoState = StringField()
    tz = StringField()
    geoCity = StringField()
    weatherRef = StringField()
    weather = StringField()
    floor = StringField()


class Rec(TimestampedDocument):
    """A wrapper around the RecInstance. This should be removed and simply be part of the
    site document."""
    meta = {
        'collection': 'rec',
        'indexes': ['ref_id']
    }

    # external reference ID
    ref_id = StringField(required=True)
    site = ReferenceField(Site)

    rec = EmbeddedDocumentField(RecInstance)


class Model(TimestampedDocument):
    meta = {'collection': 'model'}

    path = StringField(required=True, max_length=255)


class Run(TimestampedDocument):
    meta = {
        'collection': 'run',
        'indexes': ['ref_id'],
    }

    # external ID used to track this object
    ref_id = StringField(required=True)
    site = ReferenceField(Site)
    model = ReferenceField(Model)

    job_history = ListField(StringField(max_length=255))
    # TODO: convert sim_time to an actual type
    sim_time = DynamicField(default=None)
    sim_type = StringField(required=True, choices=SimType.possible_enums_as_string(), max_length=255)
    # TODO: add in choices for status
    status = StringField(required=True, max_length=255)

    error_log = StringField(required=True, max_length=1024)


class Simulation(TimestampedDocument):
    meta = {'collection': 'simulation'}

    id = IntField(required=True, primary_key=True)
    name = StringField(required=True, max_length=255)
    site = ReferenceField(Site)

    run = ReferenceField(Run)
    # TODO: convert sim_time to an actual type
    sim_time = DynamicField()
    sim_status = StringField(required=True, choices=["Complete"], max_length=255)

    results = DictField()


class Point(TimestampedDocument):
    meta = {
        'collection': 'point',
        'indexes': ['run_id', 'ref_id'],
    }

    # External reference ID
    ref_id = StringField(required=True)
    name = StringField(required=True, max_length=255)
    run_id = ReferenceField(Run)
    point_type = StringField(required=True, choices=["Input", "Output", "Bidirectional"], max_length=50)
    key = StringField()
    value = DynamicField()
