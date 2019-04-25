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
        #print ('initial response: ', json)
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
        #print('second response: ', response.text)
        #payload = {'name': siteRef} 
        response = requests.get(self.url+'/api/nav')
        #print('third response: ', response.text )   
        r = response.text
        r = r.splitlines()
        line_seek = r[-1].split(',')
        siteref = line_seek[-1].replace('@','')
        #print (siteref)
        self.siteref = siteref
        return (self.siteref, self.modelname)

    # Start a simulation for model identified by id. The id should corrsespond to 
    # a return value from the submit method
    # sim_params should be parameters such as start_time, end_time, timescale,
    # and others. The details need to be further defined and documented
    def start(self,  **sim_params):
        
        time_scale     = sim_params["time_scale"]
        start_datetime = sim_params["start_datetime"]
        end_datetime   = sim_params["end_datetime"]
        realtime       = sim_params["realtime"]
        
        mutation = 'mutation {\n' + ' runSite(siteRef: "%s",\n startDatetime: "%s",\n endDatetime: "%s",\n timescale: "%s",\n realtime: "%s") \n}' % (self.siteref, start_datetime, end_datetime, time_scale, realtime)
          
        mutation = mutation.replace('timescale: "5"', 'timescale: 5')
        #print (mutation)
        
        payload = {'query': mutation}
         
        response = requests.post(self.url + '/graphql', data=payload ) 
        print('starting simu API response: \n')
        print(response.text)
        print (response.status_code)

      


    # Stop a simulation for model identified by id
    def stop(self, id):    
        mutation = 'mutation { stopSite(siteRef: "%s") }' % (id)

        payload = {'query': mutation}
        
        response = requests.post(self.url + '/graphql', json=payload )
        print('stopping simu API response: \n')
        print(response.text)


    # remove a site for model identified by id
    def remove(self, id):
        mutation = 'mutation { removeSite(siteRef: "%s") }' % (id)

        payload = {'query': mutation}

        response = requests.post(self.url + '/graphql', json=payload )
        print('remove site API response: \n')
        print(response.text) 
       
 
    # Return the input values for simulation identified by id,
    # in the form of a dictionary. See setInputs method for dictionary format
    def inputs(self):
          
        viewer = '{viewer {\n'+ ' sites(\n ' + ('  siteRef: "%s"') %(self.siteref) +'){\n ' + ' points {\n' + '  dis\n' + '  tags{\n' + '   key' +' '+ 'value' + '\n}}}}}'

        payload = {'query': viewer}
        response = requests.post(self.url+'/graphql', json=payload)
        response = response.json()
        response = response["data"]
        response = response["viewer"]
        response = response["sites"]
        response = response[0]
        response = response["points"]
        input_map={}
        for x in response:
            var_name = x['dis']
            tags = x['tags']
           
            for y in tags: 
                if y['key']=="id":
                    var_id = y['value']
                if y['key']=="curVal":
                    print ( y['value'] )
                #if y['key']=="writable":
                #    input_map[var_id] = var_name
            input_map[var_id] = var_name
        self.inputs = input_map
        print('hey input-map: ',input_map)
        return self.inputs

    # Set inputs for model identified by id
    # The inputs argument should be a dictionary of 
    # with the form
    # inputs = {
    #  input_name: { level_1: value_1, level_2: value_2...},
    #  input_name2: { level_1: value_1, level_2: value_2...}
    # }
    def setInputs(self, id, **user_inputs): 
        url    = "http://localhost:80/api/pointWrite"
        header = { "Accept":"application/json", "Content-Type":"application/json; charset=utf-8" }
        for var in user_inputs.keys():
            value_inputs = user_inputs[var]
            for level in value_inputs.keys():
                the_value = value_inputs[level]
                data = json.dumps(
                       {
                          "meta": {"ver":"2.0"},
                          "rows": [ { "id" :"r:" + id, \
                          "level": "n:"+str(level), \
                          "who" : "s:" , \
                          "val" : "n:"+str(the_value),\
                          "duration": "s:"
                                    }
                                  ],
                          "cols": [ {"name":"id"}, {"name":"level"}, {"name":"val"}, {"name":"who"}, {"name":"duration"} ]
                       }
                       )
                writing_response = requests.post(url=url, headers=header, data=data)
        if writing_response.status_code==200:
            print("Congratulations! Your inputs were applied!")
            print (writing_response.text)                
        else:
            print("Poor Boy! You inputs have some issue!")        


    # Return a dictionary of the output values
    # result = {
    # output_name1 : output_value1,
    # output_name2 : output_value2
    #}
    def outputs(self, id):
        
        url    = "http://localhost:80/api/read"
        header = { "Accept":"application/json", "Content-Type":"text/zinc" }
        header2 = { "Accept":"application/json", "Content-Type":"application/json; charset=utf-8" }
        payload = 'ver:"2.0"\n' + 'filter,limit\n' + ('id==@"%s"')%(id) + '\,1000'
        data = json.dumps(
                       {
                          "meta": {"ver":"2.0"},
                          "rows": [ { "id" :"r:" + id, \
                          "who" : "s:" , \
                          "val" : "n:" , \
                          "duration": "s:"
                                    }
                                  ],
                          "cols": [ {"name":"id"}, {"name":"val"}, {"name":"who"}, {"name":"duration"} ]
                       }
                       )
 
        reading_response = requests.post(url=url, headers=header2, data=data)

        
        if reading_response.status_code==200:
            print("Congratulations! Outputs were retrieved!")
            print (reading_response.text)
        else:
            print("Poor boy, outputs have issues!")
     


