import datetime

from mongoengine import (
    DateTimeField,
    DictField,
    Document,
    IntField,
    ListField,
    StringField
)


class TimestampedDocument(Document):
    """Create a class to save the created_at and updated_at fields automatically"""
    meta = {'allow_inheritance': True, 'abstract': True}

    created_at = DateTimeField(required=True, default=datetime.datetime.now)
    updated_at = DateTimeField(required=True, default=datetime.datetime.now)

    def save(self, force_insert=False, validate=True, clean=True, write_concern=None, cascade=None,
             cascade_kwargs=None, _refs=None, save_condition=None, signal_kwargs=None, **kwargs,):
        self.updated_at = datetime.datetime.now()
        return super().save(
            force_insert, validate, clean, write_concern, cascade, cascade_kwargs, _refs, save_condition,
            signal_kwargs, **kwargs
        )


class Site(TimestampedDocument):
    meta = {'collection': 'site'}

    id = IntField(required=True, primary_key=True)
    name = StringField(required=True, max_length=255)
    haystack = DictField()

    # for testing...
    tags = ListField(StringField(max_length=30))
