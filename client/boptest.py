import uuid
import requests
import json
import os
import boto3
from minio import Minio
from requests_toolbelt.multipart.encoder import MultipartEncoder
from shutil import copyfile
#import getpass
from pymongo import MongoClient
import testcase


class Boptest:

    # The url argument is the address of the Boptest server
    # default should be http://localhost/api
    def __init__(self, url):
        if url != "http://localhost/api":
            print("your specified url is incorrect!")
            self.url = "http://localhost/api"
        else:
            self.url = url
        
    # The path argument should be a filesystem path to an fmu
    # this should be equivalent to uploading a file through 
    # Boptest UI. See code here 
    # https://github.com/NREL/alfalfa/blob/develop/web/components/Upload/Upload.js#L127
    # return value should be a string unique identifier for the model
    def submit(self, path):
        #uploadID = str(uuid.uuid1())
        uploadID = '1decd0bb-50d4-11e9-a0b0-08002760ddd3'
        self.uploadID = uploadID
        print (uploadID)
        if '/' not in path: 
            model_name = path #it means the fmu model is in the same folder
        else:
            path_split = path.split('/') 
            model_name = path_split[-1]
        
        self.model_name =model_name
     
        upload_dst = 'uploads' + '/' + uploadID + '/' + model_name
        if not os.path.exists(upload_dst):
            copyfile("sharedfiles/wrapped.fmu", upload_dst)

        self.upload_dst = upload_dst
        
        payload = {'name': upload_dst}
        header = {'content-type':'application/json'}
        
        #response = requests.get(self.url, params=payload, headers=header)
        response = requests.get(self.url,  headers=header)
        if response.ok:
            print ('status: ',response.status_code)
            #print (response.content)
        else:
            print('status: ',response.status_code)
            #print (response)
        
        if response.status_code==200:
           return self.upload_dst 
        else:
           print("http requests have issues!")


    # make http requests to upload file
    def upload_model_http(self, path):
        upload_dst = self.submit(path)
        if upload_dst:
            tmp = upload_dst.split("/")
            model_name = tmp[-1]
            upload_id  = tmp[-2]
         
             
            model = MultipartEncoder(fields={'name':('wrapped.fmu', \
                                                 open(upload_dst,'rb')), 'Content-Type': ('application/json; charset=utf-8')
                                        }
                                 )
                       
            header = {'Content-type': 'application/json; charset=utf-8'}
            http_url = 'http://localhost/upload-url'            
            payload = {'name': upload_dst }
            r = requests.post(http_url, data=model, \
                              headers={'Content-Type': model.content_type})
            #r = requests.post(http_url, data = payload, headers=header)
            print ("......http requests ......") 
            print (r.text)
            print(r.status_code)
            
            
    #use Minio client to upload file
    def upload_model_s3(self, path):
        tmp = path.split("/")
        model_name = tmp[-1]
        #print('Hey modle name: ', model_name)
        upload_id  = tmp[-2]
        
        #s3_url = 'http://minio:9000'
        s3_url = 'http://localhost/upload-url'
              
        s3 = boto3.resource('s3', 
                            region_name = 'us-east-1', 
                            endpoint_url = s3_url )

        bucket = s3.Bucket('alfalfa')
        
        upload_id = 'abcde'
        key = "uploads/%s/%s" % (upload_id, model_name)

        if not os.path.exists("uploads/"+upload_id):
            os.makedirs("uploads/"+upload_id)

        if not os.path.isfile(key):
            copyfile("sharedfiles/wrapped.fmu", key)

        #filedata = open(model_name, 'rb')        
        bucket.upload_file(key,'alfalfa')
        print ("...... s3 request ......")




    # Start a simulation for model identified by id. The id should corrsespond to 
    # a return value from the submit method
    # sim_params should be parameters such as start_time, end_time, timescale,
    # and others. The details need to be further defined and documented
    def start(self,  **sim_params):
        site_ref = 'id'
        real_time_flag = False
        time_scale = 5
        user_start_Datetime = sim_params['start_datetime']
        user_end_Datetime = sim_params['end_datetime']
        sim_path = 'simulate/'
        if not os.path.exists(sim_path):
            os.makedirs(sim_path)
            

        fmupath = os.path.join(os.getcwd())+'/'+sim_path+'model.fmu'
        if not os.path.isfile(fmupath):
            copyfile("sharedfiles/wrapped.fmu", fmupath)

        #tagpath = os.path.join(os.getcwd())+'/'+sim_path+'tags.json'
        #if not os.path.isfile(tagpath):
        #    copyfile("sharedfiles/tags.json", tagpath)

        print ("hey fmupath: ", fmupath)
        mongo_client = MongoClient('mongodb://mongo:27017/')
        mongodb = mongo_client['admin']
        recs = mongodb.recs
        recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Running"}}, False)

        config = { 'fmupath': fmupath, 'step': 60 }
        
                
        tc = testcase.TestCase(config)
        u = {}
        #run the FMU simulation
        kstep=0
        stop = False
        simtime = 0
        while simtime < 120 and not stop:
            y_output = tc.advance(u)
            simtime = tc.final_time
            output_time_string = 's:%s' %(simtime)
            recs.update_one( {"_id": site_ref}, { "$set": {"rec.datetime": output_time_string, "rec.simStatus":"s:Running"} } )

        return 0
        
    
    def get_tag_data(self, tag_filepath):
        '''
        Purpose: retrieving the haystack tagged data, 
              which are model-exchange variables in FMU. 
        Inputs:  a json file containing all the tagged data.
        Returns: a list for all the tagged data, with the tagging properties
              like id, dis, site_ref, etc...
        '''
        with open( tag_filepath ) as json_data:
            tag_data = json.load(json_data)
     
        return tag_data


    #This is the function to create tags
    def create_DisToID_dictionary(self, tag_filepath):
        '''
        Purpose: matching the haystack display-name and IDs
        Inputs:  a json file containing all the tagged data
        Returns: a dictionary mathching all display-names and IDs
             a dictionary matching all inputs and IDs
             a dictionary matching all outputs and IDs 
             a dictionary matching all IDs and display-names 
        '''
        dis_and_ID={}
        inputs_and_ID = {}
        outputs_and_ID = {}
        id_and_dis={}

        tag_data = get_tag_data(tag_filepath)

        for point in tag_data:
            var_name = point['dis'].replace('s:','')
            var_id = point['id'].replace('r:','')

            dis_and_ID[var_name] = var_id
            id_and_dis[var_id] = var_name

            if 'writable' in point.keys():
                #it means it is a input variable.
                #clean the var-name, discarding: ':input','s:','r:'
                #input_var = var_name.replace(':input','')
                #input_var = input_var.replace('s:','')
                inputs_and_ID[var_name] = var_id

            if 'writable' not in point.keys() and 'point' in point.keys():
                #it means it is an output variable, plus not sitetag.
                #clean the var-name, discarding: ':output','s:','r:'
                #output_var = var_name.replace(':output','')
                #output_var = output_var.replace('s:','')
                outputs_and_ID[var_name] = var_id

        return (dis_and_ID, inputs_and_ID, outputs_and_ID, id_and_dis)



    # Stop a simulation for model identified by id
    def stop(self, id):
        pass

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


###############################################################################
url = 'http://localhost/api'
boptest = Boptest(url)
path_fmu = '/home/mindcoder/alfalfa/worker/wrapped.fmu' 
#boptest.submit(path_fmu)
#boptest.upload_model_http(path_fmu)
#boptest.upload_model_s3(path_fmu)
sim_param={'start_datetime':1 , 'end_datetime':2 }
boptest.start(**sim_param)
print ("Good Job!!! You made the Dockerfile-client work!!!")
