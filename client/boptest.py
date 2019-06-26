import uuid
import requests
import json
import os
import time
from requests_toolbelt import MultipartEncoder

class Boptest:

    # The url argument is the address of the Boptest server
    # default should be http://localhost/api
    def __init__(self, url='http://localhost'):
        self.url = url
         
    def status(self, siteref):
        status = ''

        query = '{ viewer{ sites(siteRef: "%s") { simStatus } } }' % siteref
        response = requests.post(self.url + '/graphql', json={'query': query})
        j = json.loads(response.text)
        sites = j["data"]["viewer"]["sites"]
        if sites: 
            status = sites[0]["simStatus"]

        return status   

    def wait(self, siteref, desired_status):
        sites = []

        attempts = 0;
        while attempts < 240:
            attempts = attempts + 1
            current_status = self.status(siteref)

            if desired_status:
                if current_status == desired_status:
                    break
            elif current_status:
                break
            time.sleep(0.1)

    # this should be equivalent to uploading a file through 
    # Boptest UI. See code here 
    # https://github.com/NREL/alfalfa/blob/develop/web/components/Upload/Upload.js#L127
    # return value should be a string unique identifier for the model
    def submit(self, path):
        filename = os.path.basename(path)
        uid = str(uuid.uuid1())
        
        key = 'uploads/' + uid + '/' + filename
        payload = {'name': key}

        # Get a template for the file upload form data
        # The server has an api to give this to us
        response = requests.post(self.url + '/upload-url', json=payload)
        
        json = response.json()
        postURL = json['url']
        formData = json['fields']
        formData['file'] = ('filename', open(path, 'rb'))

        # Use the form data from the server to actually upload the file
        encoder = MultipartEncoder(fields=formData)
        response = requests.post(postURL, data=encoder, headers={'Content-Type': encoder.content_type})

        # After the file has been uploaded, then tell BOPTEST to process the site
        # This is done not via the haystack api, but through a graphql api
        mutation = 'mutation { addSite(osmName: "%s", uploadID: "%s") }' % (filename, uid)
        response = requests.post(self.url + '/graphql', json={'query': mutation})

        self.wait(uid, "Stopped")

        return uid

    # Start a simulation for model identified by id. The id should corrsespond to 
    # a return value from the submit method
    # kwargs are timescale, start_datetime, end_datetime, realtime, external_clock
    def start(self,  site_id, **kwargs):
        mutation = 'mutation { runSite(siteRef: "%s"' % site_id

        if "timescale" in kwargs:
            mutation = mutation + ', timescale: %s' % sim_params["timescale"]
        if "start_datetime" in kwargs:
            mutation = mutation + ', startDatetime: "%s"' % sim_params["start_datetime"]
        if "end_datetime" in kwargs:
            mutation = mutation + ', endDatetime: "%s"' % sim_params["end_datetime"]
        if "realtime" in kwargs:
            mutation = mutation + ', realtime: %s' % sim_params["realtime"]
        if "external_clock" in kwargs:
            mutation = mutation + ', externalClock: %s' % kwargs["external_clock"]

        mutation = mutation + ') }'

        response = requests.post(self.url + '/graphql', json={'query': mutation})
        self.wait(site_id, "Running")

    def advance(self, siteids):
        ids = ', '.join('"{0}"'.format(s) for s in siteids)
        mutation = 'mutation { advance(siteRefs: [%s]) }' % (ids)
        payload = {'query': mutation}
        response = requests.post(self.url + '/graphql', json=payload )

    # Stop a simulation for model identified by id
    def stop(self, siteid):    
        mutation = 'mutation { stopSite(siteRef: "%s") }' % (siteid)
        payload = {'query': mutation}
        response = requests.post(self.url + '/graphql', json=payload )

        self.wait(siteid, "Stopped")


    ### remove a site for model identified by id
    ##def remove(self, id):
    ##    mutation = 'mutation { removeSite(siteRef: "%s") }' % (id)

    ##    payload = {'query': mutation}

    ##    response = requests.post(self.url + '/graphql', json=payload )
    ##    print('remove site API response: \n')
    ##    print(response.text) 
    ##   

    # Set inputs for model identified by display name
    # The inputs argument should be a dictionary of 
    # with the form
    # inputs = {
    #  input_name: value1,
    #  input_name2: value2
    # }
    def setInputs(self, siteid, inputs): 
        for key,value in inputs.items():
            if value or (value == 0):
                mutation = 'mutation { writePoint(siteRef: "%s", pointName: "%s", value: %s, level: 1 ) }' % (siteid, key, value)
            else:
                mutation = 'mutation { writePoint(siteRef: "%s", pointName: "%s", level: 1 ) }' % (siteid, key)
            response = requests.post(self.url + '/graphql', json={'query': mutation})

    # Return a dictionary of the output values
    # result = {
    # output_name1 : output_value1,
    # output_name2 : output_value2
    #}
    def outputs(self, siteid):
        query = 'query { viewer { sites(siteRef: "%s") { points(cur: true) { dis tags { key value } } } } }' % (siteid)
        payload = {'query': query}
        response = requests.post(self.url + '/graphql', json=payload )

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
    #}
    def inputs(self, siteid):
        query = 'query { viewer { sites(siteRef: "%s") { points(writable: true) { dis tags { key value } } } } }' % (siteid)
        payload = {'query': query}
        response = requests.post(self.url + '/graphql', json=payload )

        j = json.loads(response.text)
        points = j["data"]["viewer"]["sites"][0]["points"]
        result = {}

        for point in points:
            tags = point["tags"]
            for tag in tags:
                if tag["key"] == "writeVal":
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
        
     

