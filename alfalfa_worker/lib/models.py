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
    meta = {
        'collection': 'site',
        'indexes': ['ref_id'],
    }

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

    # This included the entire list of tags that are in haystack's tags.txt file.
    # TODO: maybe we need to make this a dynamic field: https://docs.mongoengine.org/guide/defining-documents.html#dynamic-document-schemas
    id = StringField()

    absorption = StringField()
    ac = StringField()
    active = StringField()
    ahu = StringField()
    ahuRef = StringField()
    air = StringField()
    airCooled = StringField()
    angle = StringField()
    apparent = StringField()
    area = StringField()
    avg = StringField()

    barometric = StringField()
    blowdown = StringField()
    boiler = StringField()
    bypass = StringField()

    dis = StringField()

    centrifugal = StringField()
    chilled = StringField()
    chilledBeamZone = StringField()
    chilledWaterCool = StringField()
    chilledWaterPlant = StringField()
    chilledWaterPlantRef = StringField()
    chiller = StringField()
    circ = StringField()
    circuit = StringField()
    closedLoop = StringField()
    cloudage = StringField()
    cmd = StringField()
    co = StringField()
    co2 = StringField()
    coldDeck = StringField()
    condensate = StringField()
    condenser = StringField()
    connection = StringField()
    constantVolume = StringField()
    cool = StringField()
    coolOnly = StringField()
    cooling = StringField()
    coolingCapacity = StringField()
    coolingTower = StringField()
    cur = StringField()
    current = StringField()
    curErr = StringField()
    # curVal and curStatus now only live in Redis, remove from here
    # curVal = StringField()
    # curStatus = StringField()

    damper = StringField()
    # Not in Haystack tags
    datetime = StringField()
    dc = StringField()
    delta = StringField()
    device = StringField()
    device1Ref = StringField()
    device2Ref = StringField()
    dew = StringField()
    directZone = StringField()
    direction = StringField()
    dis = StringField()
    discharge = StringField()
    diverting = StringField()
    domestic = StringField()
    dualDuct = StringField()
    ductArea = StringField()
    dxCool = StringField()

    effective = StringField()
    efficiency = StringField()
    elec = StringField()
    elecHeat = StringField()
    elecMeterLoad = StringField()
    elecMeterRef = StringField()
    elecPanel = StringField()
    elecPanelOf = StringField()
    elecReheat = StringField()
    enable = StringField()
    energy = StringField()
    entering = StringField()
    enum = StringField()
    equip = StringField()
    equipRef = StringField()
    evaporator = StringField()
    exhaust = StringField()
    export = StringField()

    faceBypass = StringField()
    fan = StringField()
    fanPowered = StringField()
    fcu = StringField()
    filter = StringField()
    # added tag
    floor = StringField()
    # added tag
    floorRef = StringField()
    flow = StringField()
    flue = StringField()
    freezeStat = StringField()
    freq = StringField()

    gas = StringField()
    gasHeat = StringField()
    gasMeterLoad = StringField()
    geoAddr = StringField()
    geoCity = StringField()
    geoCoord = StringField()
    geoCountry = StringField()
    geoCounty = StringField()
    geoPostalCode = StringField()
    geoState = StringField()
    geoStreet = StringField()

    header = StringField()
    heat = StringField()
    heatExchanger = StringField()
    heatPump = StringField()
    heatWheel = StringField()
    heating = StringField()
    his = StringField()
    hisErr = StringField()
    hisInterpolate = StringField()
    hisStatus = StringField()
    hisTotalized = StringField()
    hot = StringField()
    hotDeck = StringField()
    hotWaterHeat = StringField()
    hotWaterPlant = StringField()
    hotWaterPlantRef = StringField()
    hotWaterReheat = StringField()
    humidifier = StringField()
    humidity = StringField()
    hvac = StringField()

    imbalance = StringField()
    irradiance = StringField()
    isolation = StringField()

    kind = StringField()

    leaving = StringField()
    level = StringField()
    lightLevel = StringField()
    lighting = StringField()
    lights = StringField()
    lightsGroup = StringField()
    load = StringField()

    mag = StringField()
    makeup = StringField()
    mau = StringField()
    max = StringField()
    maxVal = StringField()
    meter = StringField()
    min = StringField()
    minVal = StringField()
    mixed = StringField()
    mixing = StringField()
    multiZone = StringField()

    net = StringField()
    network = StringField()
    networkRef = StringField()
    neutralDeck = StringField()

    occ = StringField()
    occupancyIndicator = StringField()
    occupied = StringField()
    oil = StringField()
    openLoop = StringField()
    outside = StringField()

    parallel = StringField()
    perimeterHeat = StringField()
    pf = StringField()
    phase = StringField()
    point = StringField()
    # added tag
    position = StringField()
    power = StringField()
    precipitation = StringField()
    pressure = StringField()
    pressureDependent = StringField()
    pressureIndependent = StringField()
    primaryFunction = StringField()
    primaryLoop = StringField()
    protocol = StringField()
    pump = StringField()

    reactive = StringField()
    reciprocal = StringField()
    refrig = StringField()
    reheat = StringField()
    reheating = StringField()
    return_ = StringField()
    rooftop = StringField()
    run = StringField()

    screw = StringField()
    secondaryLoop = StringField()
    sensor = StringField()
    series = StringField()
    # added tag
    simStatus = StringField()
    # added tag
    simType = StringField()
    singleDuct = StringField()
    site = StringField()
    siteMeter = StringField()
    sitePanel = StringField()
    siteRef = StringField()
    solar = StringField()
    sp = StringField()
    speed = StringField()
    stage = StringField()
    standby = StringField()
    steam = StringField()
    steamHeat = StringField()
    steamMeterLoad = StringField()
    steamPlant = StringField()
    steamPlantRef = StringField()
    # added tag
    step = StringField()
    subPanelOf = StringField()
    submeterOf = StringField()
    sunrise = StringField()

    tank = StringField()
    temp = StringField()
    thd = StringField()
    total = StringField()
    tripleDuct = StringField()
    tz = StringField()

    unit = StringField()
    unocc = StringField()
    uv = StringField()

    valve = StringField()
    variableVolume = StringField()
    vav = StringField()
    vavMode = StringField()
    vavZone = StringField()
    vfd = StringField()
    visibility = StringField()
    volt = StringField()
    volume = StringField()

    water = StringField()
    waterCooled = StringField()
    waterMeterLoad = StringField()
    weather = StringField()
    weatherCond = StringField()
    weatherPoint = StringField()
    weatherRef = StringField()
    wetBulb = StringField()
    wind = StringField()
    writable = StringField()
    writeErr = StringField()
    writeLevel = StringField()
    writeStatus = StringField()
    writeVal = StringField()

    yearBuilt = StringField()

    zone = StringField()

    def __init__(self, *args, **kwargs):
        # if an arg is coming in with `return` then replace it with `return_`
        # to allow it to persist correctly in the database. Same with `import`
        if 'return' in kwargs:
            kwargs['return_'] = kwargs.pop('return')

        if 'import' in kwargs:
            kwargs['import_'] = kwargs.pop('import')

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
