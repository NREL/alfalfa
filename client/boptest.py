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
        formData['file'] = open(path, 'rb')

        # Use the form data from the server to actually upload the file
        encoder = MultipartEncoder(fields=formData)
        requests.post(postURL, data=encoder, headers={'Content-Type': encoder.content_type})

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
        #mutation = 'mutation { runSite(siteRef: "%s", externalClock: true) }' % site_id
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
 
    ### Return the input values for simulation identified by id,
    ### in the form of a dictionary. See setInputs method for dictionary format
    ##def inputs(self, siteref):
    ##      
    ##    viewer = '{viewer {\n'+ ' sites(\n ' + ('  siteRef: "%s"') %(siteref) +'){\n ' + ' points {\n' + '  dis\n' + '  tags{\n' + '   key' +' '+ 'value' + '\n}}}}}'

    ##    payload = {'query': viewer}
    ##    
    ##    response = requests.post(self.url+'/graphql', json=payload)
    ##    response = response.json()
    ##    response = response["data"]
    ##    response = response["viewer"]
    ##    response = response["sites"]
    ##    response = response[0]
    ##    response = response["points"]
    ##    input_map={}
    ##    for x in response:
    ##        var_name = x['dis']
    ##        tags = x['tags']
    ##       
    ##        for y in tags: 
    ##            if y['key']=="id":
    ##                var_id = y['value']
    ##                if y['key']=="curVal":
    ##                    print ( y['value'] )
    ##                    #if y['key']=="writable":
    ##                    #    input_map[var_id] = var_name
    ##        input_map[var_id] = var_name
    ##    
    ##    self.inputs = input_map
    ##    print('hey input-map: ',input_map)
    ##    return self.inputs

    ### Set inne_sputs for model identified by id
    ### The inputs argument should be a dictionary of 
    ### with the form
    ### inputs = {
    ###  input_name: { level_1: value_1, level_2: value_2...},
    ###  input_name2: { level_1: value_1, level_2: value_2...}
    ### }
    ##def setInputs(self, id, **user_inputs): 
    ##    url    = "http://localhost:80/api/pointWrite"
    ##    header = { "Accept":"application/json", "Content-Type":"application/json; charset=utf-8" }
    ##    for var in user_inputs.keys():
    ##        value_inputs = user_inputs[var]
    ##        for level in value_inputs.keys():
    ##            the_value = value_inputs[level]
    ##            data = json.dumps(
    ##                   {
    ##                      "meta": {"ver":"2.0"},
    ##                      "rows": [ { "id" : id, \
    ##                      "level": "n:"+str(level), \
    ##                      "who" : "s:" , \
    ##                      "val" : "n:"+str(the_value),\
    ##                      "duration": "s:"
    ##                                }
    ##                              ],
    ##                      "cols": [ {"name":"id"}, {"name":"level"}, {"name":"val"}, {"name":"who"}, {"name":"duration"} ]
    ##                   }
    ##                   )
    ##            writing_response = requests.post(url=url, headers=header, data=data)
    ##    if writing_response.status_code==200:
    ##        print("Congratulations! Your inputs were applied!")
    ##        print (writing_response.text)                
    ##    else:
    ##        print("Poor Boy! You inputs have some issue!")        


    ### Return a dictionary of the output values
    ### result = {
    ### output_name1 : output_value1,
    ### output_name2 : output_value2
    ###}
    ##def outputs(self, id):
    ##    
    ##    url    = "http://localhost:80/api/read"
    ##    header = { "Accept":"application/json", "Content-Type":"text/zinc" }
    ##    header2 = { "Accept":"application/json", "Content-Type":"application/json; charset=utf-8" }
    ##    payload = 'ver:"2.0"\n' + 'filter,limit\n' + ('id==@"%s"')%(id) + '\,1000'
    ##    data = json.dumps(
    ##                   {
    ##                      "meta": {"ver":"2.0"},
    ##                      "rows": [ { "id" :  id, \
    ##                      "who" : "s:" , \
    ##                      "val" : "n:" , \
    ##                      "duration": "s:"
    ##                                }
    ##                              ],
    ##                      "cols": [ {"name":"id"}, {"name":"val"}, {"name":"who"}, {"name":"duration"} ]
    ##                   }
    ##                   )
    ##    updating = self.init_check_updating()
    ##    if updating !='"NaN"' or '""': 
    ##        reading_response = requests.post(url=url, headers=header2, data=data)
    ##        if reading_response.status_code==200:
    ##            print("Congratulations! Outputs were retrieved!")
    ##            print (reading_response.text)
    ##            return reading_response.text

    ##        else:
    ##            print("Poor boy, outputs have issues!")
     

