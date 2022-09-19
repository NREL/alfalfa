import datetime
import json

from mongoengine import (
    CASCADE,
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

    def to_dict(self):
        """Override the to_dict method to include to convert specific fields correctly.
        e.g., created and modified should be converted to iso8601 strings.
        """
        created = self.created.isoformat()
        modified = self.modified.isoformat()

        data = json.loads(self.to_json())

        data['created'] = created
        data['modified'] = modified
        return data


class Site(TimestampedDocument):
    meta = {'collection': 'site'}

    # external reference ID
    ref_id = StringField(required=True, index=True)
    name = StringField(required=True, max_length=255)
    haystack_raw = ListField(DictField())

    # In old database the first recs is the site, this is now moved to the
    # site object in the database. Need to type this eventually
    dis = StringField()
    site = StringField()
    area = StringField()
    geo_city = StringField()
    geo_coord = StringField()
    geo_country = StringField()
    geo_state = StringField()
    tz = StringField()
    weather_ref = StringField()
    sim_status = StringField()
    sim_type = StringField()

    def recs(self, **kwargs: dict):  # -> list[Rec]:
        """Return list of all the recs for the site

        Args:
            **kwargs: Additional arguments to pass to the Rec.objects.filter() method.

        Returns:
            list: Rec objects

        """
        return Rec.objects.filter(site=self, **kwargs)


class RecInstance(EmbeddedDocument):
    """This is a flat haystack representation of a point. Right now this stores the union of any
    value that is expected. Many of these fields are probably not used anymore on this object
    (e.g., simStatus, step), but they are still included because the code base is reading/writing
    the valued. For example, it is unsetting `step` even though it doesn't appear to be written to."""

    # TODO: maybe we need to make this a dynamic field: https://docs.mongoengine.org/guide/defining-documents.html#dynamic-document-schemas
    id = StringField()
    dis = StringField()
    siteRef = StringField()
    point = StringField()
    cur = StringField()
    curVal = StringField()
    curErr = StringField()
    curStatus = StringField()
    kind = StringField()
    site = StringField()
    simStatus = StringField()
    step = StringField()
    datetime = StringField()
    simType = StringField()
    writable = StringField()
    writeStatus = StringField()
    writeLevel = StringField()
    writeVal = StringField()
    area = StringField()
    geoCoord = StringField()
    geoCountry = StringField()
    geoState = StringField()
    tz = StringField()
    geoCity = StringField()
    weatherRef = StringField()
    weather = StringField()
    floor = StringField()
    temp = StringField()
    air = StringField()
    equipRef = StringField()
    discharge = StringField()
    sensor = StringField()
    unit = StringField()
    floorRef = StringField()
    pressure = StringField()
    humidity = StringField()
    flow = StringField()
    position = StringField()
    outside = StringField()
    damper = StringField()
    cmd = StringField()
    mixed = StringField()
    return_ = StringField()
    exhaust = StringField()
    volume = StringField()
    zone = StringField()
    cooling = StringField()
    heating = StringField()
    directZone = StringField()
    sp = StringField()
    hvac = StringField()
    ahu = StringField()
    equip = StringField()

    def __init__(self, *args, **kwargs):
        # if an arg is coming in with `return` then replace it with `return_`
        # to allow it to persist correctly in the database
        if 'return' in kwargs:
            kwargs['return_'] = kwargs.pop('return')

        super().__init__(*args, **kwargs)


class Rec(TimestampedDocument):
    """A wrapper around the RecInstance. This should be removed and simply be part of the
    site document."""
    meta = {
        # TODO: convert back to rec after the refactor is complete; requires front end change
        'collection': 'recs',
        'indexes': ['ref_id']
    }

    # external reference ID
    ref_id = StringField(required=True)
    site = ReferenceField(Site, required=True, reverse_delete_rule=CASCADE)
    # save the site ID as a string too, for now, because the front end isn't
    # currently saving as a reference.
    site_id = StringField()

    rec = EmbeddedDocumentField(RecInstance)

    # def site(self):
    # return self.site


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

    # The site is required but it only shows up after the haystack points
    # are extracted.
    site = ReferenceField(Site, reverse_delete_rule=CASCADE)
    model = ReferenceField(Model, reverse_delete_rule=CASCADE)

    job_history = ListField(StringField(max_length=255))

    sim_time = DynamicField(default=None)
    sim_type = StringField(required=True, choices=SimType.possible_enums_as_string(), max_length=255)
    # TODO: add in choices for status
    status = StringField(required=True, max_length=255)

    error_log = StringField(required=True, max_length=65535)


class Simulation(TimestampedDocument):
    meta = {'collection': 'simulation'}

    name = StringField(required=True, max_length=255)
    site = ReferenceField(Site, required=True, reverse_delete_rule=CASCADE)

    # TODO: A simulation is attached to a site, not a run, which might be right.
    # run = ReferenceField(Run)
    ref_id = StringField()

    # TODO: convert time completed to actual time (right now it is a string, mostly)
    time_completed = DynamicField()
    sim_status = StringField(required=True, choices=["Complete"], max_length=255)

    s3_key = StringField()
    results = DictField()


class Point(TimestampedDocument):
    meta = {
        'collection': 'point',
        'indexes': ['run', 'ref_id'],
    }

    # External reference ID
    ref_id = StringField()
    name = StringField(required=True, max_length=255)
    run = ReferenceField(Run, reverse_delete_rule=CASCADE)
    point_type = StringField(required=True, choices=["Input", "Output", "Bidirectional"], max_length=50)
    key = StringField()
    value = DynamicField()


class WriteArray(TimestampedDocument):
    """These data come from alfalfa_web through a direct connection to mongo"""
    meta = {
        # TODO: convert back to write_array after the refactor is complete; requires front end change
        'collection': 'writearrays',
        'indexes': ['site', 'ref_id']
    }

    ref_id = StringField()
    # is the write array really attached to a site, seems like it should be for a run of a site?
    site = ReferenceField(Site, required=True, reverse_delete_rule=CASCADE)
    # save the site ID as a string too, for now, because the front end isn't
    # currently saving as a reference.
    site_id = StringField()
    whos = ListField(DynamicField())
    values = ListField(DynamicField())
