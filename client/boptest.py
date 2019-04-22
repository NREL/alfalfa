import uuid
import requests
import json
import os
from requests_toolbelt import MultipartEncoder

class Boptest:

    # The url argument is the address of the Boptest server
    # default should be http://localhost/api
    def __init__(self, url='http://localhost'):
        self.url = url
        
    # The path argument should be a filesystem path to an fmu
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
        postURL = json['postURL']
        formData = json['formData']
        formData['file'] = open(path, 'rb')

        # Use the form data from the server to actually upload the file
        encoder = MultipartEncoder(fields=formData)
        requests.post(postURL, data=encoder, headers={'Content-Type': encoder.content_type})

        # After the file has been uploaded, then tell BOPTEST to process the site
        # This is done not via the haystack api, but through a graphql api
        mutation = 'mutation { addSite(osmName: "%s", uploadID: "%s") }' % (filename, uid)
        response = requests.post(self.url + '/graphql', json={'query': mutation})
        self.uuid = uid
        self.modelname = filename

        return (self.uuid, self.modelname)

    # Start a simulation for model identified by id. The id should corrsespond to 
    # a return value from the submit method
    # sim_params should be parameters such as start_time, end_time, timescale,
    # and others. The details need to be further defined and documented
    def start(self,  **sim_params):
        
        time_scale     = sim_params["time_scale"]
        start_datetime = sim_params["start_datetime"]
        end_datetime   = sim_params["end_datetime"]
        realtime       = sim_params["realtime"]

        mutation = 'mutation { runSite(siteRef: "%s", startDatetime: "%s", endDatetime: "%s", timescale: "%s", realtime: "%s") }' % (self.uuid, start_datetime, end_datetime, time_scale, realtime)
          
        mutation = mutation.replace('timescale: "5"', 'timescale: 5')
 
        payload = {'query': mutation}
         
        response = requests.post(self.url + '/graphql', json=payload ) 
        print('starting simu API response: \n')
        print(response.text)
      


    # Stop a simulation for model identified by id
    def stop(self, id):    
        mutation = 'mutation { stopSite(siteRef: "%s") }' % (id)

        payload = {'query': mutation}
        
        response = requests.post(self.url + '/graphql', json=payload )
        print('stopping simu API response: \n')
        print(response.text)

 
        
    # Return the input values for simulation identified by id,
    # in the form of a dictionary. See setInputs method for dictionary format
    def inputs(self, id):
        pass
    # Set inputs for model identified by id
    # The inputs argument should be a dictionary of 
    # with the form
    # inputs = {
    #  input_name: { level_1: value_1, level_2: value_2...},
    #  input_name2: { level_1: value_1, level_2: value_2...}
    # }
    def setInputs(self, id, **inputs):
        pass
    # Return a dictionary of the output values
    # result = {
    # output_name1 : output_value1,
    # output_name2 : output_value2
    #}
    def outputs(self, id):
        pass

