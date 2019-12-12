import uuid
import requests
import json
import os
import time
from requests_toolbelt import MultipartEncoder
from multiprocessing import Pool
from functools import partial
import copy
from collections import OrderedDict


class Boptest:

    # The url argument is the address of the Boptest server
    # default should be http://localhost/api
    def __init__(self, url='http://localhost'):
        self.url = url

    def status(self, siteref):
        return status(self.url, siteref)

    def wait(self, siteref, desired_status):
        return wait(self.url, siteref, desired_status)

    def submit(self, path):
        args = {"url": self.url, "path": path}
        return submit_one(args)

    def submit_many(self, paths):
        args = []
        for path in paths:
            args.append({"url": self.url, "path": path})
        p = Pool(10)
        result = p.map(submit_one, args)
        p.close()
        p.join()
        return result

    def start(self, siteid, **kwargs):
        args = {"url": self.url, "siteid": siteid, "kwargs": kwargs}
        return start_one(args)

    # Start a simulation for model identified by id. The id should corrsespond to
    # a return value from the submit method
    # kwargs are timescale, start_datetime, end_datetime, realtime, external_clock
    def start_many(self, site_ids, **kwargs):
        args = []
        for siteid in site_ids:
            args.append({"url": self.url, "siteid": siteid, "kwargs": kwargs})
        p = Pool(10)
        result = p.map(start_one, args)
        p.close()
        p.join()
        return result

    def advance(self, siteids):
        ids = ', '.join('"{0}"'.format(s) for s in siteids)
        mutation = 'mutation { advance(siteRefs: [%s]) }' % (ids)
        payload = {'query': mutation}
        response = requests.post(self.url + '/graphql', json=payload)

    def stop(self, siteid):
        args = {"url": self.url, "siteid": siteid}
        return stop_one(args)

    # Stop a simulation for model identified by id
    def stop_many(self, siteids):
        args = []
        for siteid in siteids:
            args.append({"url": self.url, "siteid": siteid})
        p = Pool(10)
        result = p.map(stop_one, args)
        p.close()
        p.join()
        return result

    # remove a site for model identified by id
    # def remove(self, id):
    ##    mutation = 'mutation { removeSite(siteRef: "%s") }' % (id)

    ##    payload = {'query': mutation}

    ##    response = requests.post(self.url + '/graphql', json=payload )
    ##    print('remove site API response: \n')
    # print(response.text)
    ##

    # Set inputs for model identified by display name
    # The inputs argument should be a dictionary of
    # with the form
    # inputs = {
    #  input_name: value1,
    #  input_name2: value2
    # }
    def setInputs(self, siteid, inputs):
        for key, value in inputs.items():
            if value or (value == 0):
                mutation = 'mutation { writePoint(siteRef: "%s", pointName: "%s", value: %s, level: 1 ) }' % (siteid, key, value)
            else:
                mutation = 'mutation { writePoint(siteRef: "%s", pointName: "%s", level: 1 ) }' % (siteid, key)
            response = requests.post(self.url + '/graphql', json={'query': mutation})

    # Return a dictionary of the output values
    # result = {
    # output_name1 : output_value1,
    # output_name2 : output_value2
    # }
    def outputs(self, siteid):
        query = 'query { viewer { sites(siteRef: "%s") { points(cur: true) { dis tags { key value } } } } }' % (siteid)
        payload = {'query': query}
        response = requests.post(self.url + '/graphql', json=payload)

        j = json.loads(response.text)
        points = j["data"]["viewer"]["sites"][0]["points"]
        result = {}

        for point in points:
            tags = point["tags"]
            for tag in tags:
                if tag["key"] == "curVal":
                    result[convert(point["dis"])] = convert(tag["value"])
                    break

        return result

    # Return a dictionary of the current input values
    # result = {
    # input_name1 : input_value1,
    # input_name2 : input_value2
    # }
    def inputs(self, siteid):
        query = 'query { viewer { sites(siteRef: "%s") { points(writable: true) { dis tags { key value } } } } }' % (siteid)
        payload = {'query': query}
        response = requests.post(self.url + '/graphql', json=payload)

        j = json.loads(response.text)
        points = j["data"]["viewer"]["sites"][0]["points"]
        result = {}

        for point in points:
            tags = point["tags"]
            for tag in tags:
                if tag["key"] == "writeStatus":
                    result[convert(point["dis"])] = convert(tag["value"])
                    break

        return result

# remove any hastack type info from value and convert numeric strings
# to python float. ie s: maps to python string n: maps to python float,
# other values are simply returned unchanged, thus retaining any haystack type prefix


def convert(value):
    if value[0:2] == 's:':
        return value[2:]
    elif value[0:2] == 'n:':
        return float(value[2:])
    else:
        return value


def status(url, siteref):
    status = ''

    query = '{ viewer{ sites(siteRef: "%s") { simStatus } } }' % siteref
    for i in range(3):
        response = requests.post(url + '/graphql', json={'query': query})
        if response.status_code == 200:
            break
    if response.status_code != 200:
        print("Could not get status")

    j = json.loads(response.text)
    sites = j["data"]["viewer"]["sites"]
    if sites:
        status = sites[0]["simStatus"]

    return status


def wait(url, siteref, desired_status):
    sites = []

    attempts = 0
    while attempts < 6000:
        attempts = attempts + 1
        current_status = status(url, siteref)

        if desired_status:
            if current_status == desired_status:
                break
        elif current_status:
            break
        time.sleep(2)


def submit_one(args):
    url = args["url"]
    path = args["path"]

    filename = os.path.basename(path)
    uid = str(uuid.uuid1())

    key = 'uploads/' + uid + '/' + filename
    payload = {'name': key}

    # Get a template for the file upload form data
    # The server has an api to give this to us
    for i in range(3):
        response = requests.post(url + '/upload-url', json=payload)
        if response.status_code == 200:
            break
    if response.status_code != 200:
        print("Could not get upload-url")

    json = response.json()
    postURL = json['url']
    formData = OrderedDict(json['fields'])
    formData['file'] = ('filename', open(path, 'rb'))

    # Use the form data from the server to actually upload the file
    encoder = MultipartEncoder(fields=formData)
    for _ in range(3):
        response = requests.post(postURL, data=encoder, headers={'Content-Type': encoder.content_type})
        if response.status_code == 204:
            break
    if response.status_code != 204:
        print("Could not post file")

    # After the file has been uploaded, then tell BOPTEST to process the site
    # This is done not via the haystack api, but through a graphql api
    mutation = 'mutation { addSite(osmName: "%s", uploadID: "%s") }' % (filename, uid)
    for _ in range(3):
        response = requests.post(url + '/graphql', json={'query': mutation})
        if response.status_code == 200:
            break
    if response.status_code != 200:
        print("Could not addSite")

    wait(url, uid, "Stopped")

    return uid


def start_one(args):
    url = args["url"]
    site_id = args["siteid"]
    kwargs = args["kwargs"]

    mutation = 'mutation { runSite(siteRef: "%s"' % site_id

    if "timescale" in kwargs:
        mutation = mutation + ', timescale: %s' % kwargs["timescale"]
    if "start_datetime" in kwargs:
        mutation = mutation + ', startDatetime: "%s"' % kwargs["start_datetime"]
    if "end_datetime" in kwargs:
        mutation = mutation + ', endDatetime: "%s"' % kwargs["end_datetime"]
    if "realtime" in kwargs:
        mutation = mutation + ', realtime: %s' % kwargs["realtime"]
    if "external_clock" in kwargs:
        mutation = mutation + ', externalClock: %s' % kwargs["external_clock"]

    mutation = mutation + ') }'

    for _ in range(3):
        response = requests.post(url + '/graphql', json={'query': mutation})
        if response.status_code == 200:
            break

    wait(url, site_id, "Running")


def stop_one(args):
    url = args["url"]
    siteid = args["siteid"]

    mutation = 'mutation { stopSite(siteRef: "%s") }' % (siteid)
    payload = {'query': mutation}
    response = requests.post(url + '/graphql', json=payload)

    wait(url, siteid, "Stopped")
