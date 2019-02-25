########################################################################################################################
#  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
#  following conditions are met:
#
#  (1) Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#  disclaimer.
#
#  (2) Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#  disclaimer in the documentation and/or other materials provided with the distribution.
#
#  (3) Neither the name of the copyright holder nor the names of any contributors may be used to endorse or promote products
#  derived from this software without specific prior written permission from the respective party.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER(S) AND ANY CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#  INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER(S), ANY CONTRIBUTORS, THE UNITED STATES GOVERNMENT, OR THE UNITED
#  STATES DEPARTMENT OF ENERGY, NOR ANY OF THEIR EMPLOYEES, BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#  USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
#  STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
########################################################################################################################

from __future__ import print_function
import os
import glob
import boto3
import tarfile
import shutil
import time
from pymongo import MongoClient
import sys
import subprocess
import logging
import re
from datetime import date, datetime, timedelta
import pytz
import calendar
import traceback
from dateutil.parser import parse
from pyfmi import load_fmu
import copy
import json


from common import *


def get_tag_data(tag_filepath):
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


def create_DisToID_dictionary(tag_filepath):
    '''
    Purpose: matching the haystack display-name and IDs
    Inputs:  a json file containing all the tagged data
    Returns: a dictionary mathching all display-names and IDs
             a dictionary matching all inputs and IDs
             a dictionary matching all outputs and IDs 
    '''
    dis_and_ID={}
    inputs_and_ID = {}
    outputs_and_ID = {}

    tag_data = get_tag_data(tag_filepath)

    for point in tag_data:
        var_name = point['dis']
        
        var_id   = point['id']
        dis_and_ID[var_name] = var_id
        
        if 'writable' in point.keys():
            #it means it is a input variable.
            #clean the var-name, discarding: ':input','s:','r:'
            input_var = var_name.replace(':input','')
            input_var = input_var.replace('s:','')
            inputs_and_ID[input_var] = var_id.replace('r:','')

        if 'writable' not in point.keys() and 'point' in point.keys():
            #it means it is an output variable, plus not sitetag.
            #clean the var-name, discarding: ':output','s:','r:'
            output_var = var_name.replace(':output','')
            output_var = output_var.replace('s:','')
            outputs_and_ID[output_var] = var_id.replace('r:','')
         
    return (dis_and_ID, inputs_and_ID, outputs_and_ID)
        

def query_var_byID(database, var_id):
    '''
    Purpose: query a variable by ID to the database
    Inputs:  database (recs in this case), and the id of the variable
    Returns: the details of the data, a dictionary with dictionary inside.
    '''
    myquery = {"_id": var_id}
    mydoc = database.find_one(myquery)
    if not mydoc:
        print(")))))) hey the query is not in the database ((((((")
    else:
        #print(")))))) hey i am querying:(((((( ", mydoc)
        pass

    return mydoc
        
        
def check_vars(var, var_string):
   '''
   Purpose: print the var details to the terminal for debugging purpose
   Inputs:  variable and variable-string
   Returns: print statement on the terminal
   '''
   print(')))))) Hey i am checking var: '+ var_string + ' ((((((: ', var)



def check_writearrays(mongodb, id_site):
   '''
   Purpose: check the writearray to see if it is there
   Inputs: mongodb and id-siteref
   Returns: contents on the writearray
   Notes: writearrays is needed in Haystack standard
   Notes2: siteRef has 'r:'; site_ref has no 'r:'. 
           They are different in the mongodb.
   '''
   write_arrays = mongodb.writearrays
   found_arrays = write_arrays.find({"siteRef": 'r:'+id_site})
   if not found_arrays:
       print ("):: hey the write_arrays is not found: ", found_arrays)
       print (type(found_arrays))
   else:
       print ("(:: hey the write_arrays is found: ", found_arrays)
       print(type(found_arrays))
       for array in found_arrays:
           print(" )))))) Hey write array: %s" % array)
           id = array.get('_id')
           print("))))))Hey the id found is: ", id)

           for val in array.get('val'):
               if val:
                   print("Congratulations!")
                   print("val: %s" % val)

               else:
                   print("writearray is empty!")

  

####################   Entry for Main Program   #####################
############################################################################



try:
    s3 = boto3.resource('s3', region_name='us-east-1', endpoint_url=os.environ['S3_URL'])

    #Initiate Mongo Database
    mongo_client = MongoClient(os.environ['MONGO_URL'])
    mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
    recs = mongodb.recs

    #get user inputs
    site_ref = sys.argv[1]
    real_time_flag = sys.argv[2]
    time_scale = int(sys.argv[3])
    user_start_Datetime = parse(sys.argv[4])
    user_end_Datetime = parse(sys.argv[5])

    #build the path for zipped-file, fmu, json
    sim_path = '/simulate'
    directory = os.path.join(sim_path, site_ref)
    tar_name = "%s.tar.gz" % site_ref
    key = "parsed/%s" % tar_name
    tarpath = os.path.join(directory, tar_name)
    fmupath = os.path.join(directory, 'model.fmu')
    tagpath = os.path.join(directory, 'tags.json')

        
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    #download the tar file and tag file
    bucket = s3.Bucket('alfalfa')
    bucket.download_file(key, tarpath)
    bucket.download_file(key, tagpath)
    
    tar = tarfile.open(tarpath)
    tar.extractall(sim_path)
    tar.close()
    
    #get the tagging id, disp, etc......
    tag_data = get_tag_data(tagpath)

    recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Running"}}, False)

    

    # Load fmu
    config = {
        'fmupath'  : fmupath,                
        'step'     : 60
    }

        
    (dis_and_id, tagid_and_inputs, tagid_and_outputs) = \
            create_DisToID_dictionary(tagpath)
 

    #initiate the testcase
    tc = testcase.TestCase(config) 
    

    #setup the fake inputs
    #send the fake inputs to the database
    u={}
    for each_input in tc.get_inputs():       
        if each_input !='time':
            u[each_input]=1.0  # fake inputs here
            input_id = tagid_and_inputs[ each_input ]
            recs.update_one( {"_id": input_id }, {"$set": {"rec.curVal":"n:%s" %u[each_input], "rec.curStatus":"s:ok","rec.cur": "m:" }} )

    #query the database for inputs
    input_queried={}
    for each_input in u.keys():
        input_id = tagid_and_inputs[ each_input ]
        input_found = query_var_byID(recs, input_id)
        input_recs = input_found[u'rec']
        input_value = float( input_recs[u'curVal'].replace('n:','') )
        input_name  = input_recs[u'dis'].replace('s:','')        
        input_queried['name'] = input_name
        input_queried['id'] = input_id
        input_queried['value'] = input_value

    check_vars(site_ref,'site_ref')
    check_writearrays(mongodb, site_ref)
    
    #run the FMU simulation
    kstep=0 
    #while tc.start_time <= 1000000000000:
    for i in range(10):
        time.sleep(5)
        tc.advance(u)
        output = tc.get_results()
        #cur_time = tc.final_time
        cur_time = datetime.utcnow(  )   
        #output_time_string = 's:%s %s' %(cur_time.isoformat(), 'Denver')
        output_time_string = 's:%s' %(tc.final_time)
        #check_vars(output_time_string, 'output_time_string') 
        recs.update_one( {"_id": site_ref}, { "$set": {"rec.datetime": output_time_string, "rec.simStatus":"s:running"} } )
        
        u_output = output['u']
        y_output = output['y']   

        for key in y_output.keys():
            value_y = y_output[key]
            
            if key!='time': 
                output_id = tagid_and_outputs[key]                          
                for cur_value in value_y:
                    recs.update_one( {"_id": output_id }, {"$set": {"rec.curVal":"n:%s" %cur_value, "rec.curStatus":"s:ok","rec.cur": "m:" }} )        
             
    #shutil.rmtree(directory)
    
    recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}, "$unset": {"rec.datetime": ""} }, False)
    recs.update_many({"_id": site_ref, "rec.cur": "m:"}, {"$unset": {"rec.curVal": "", "rec.curErr": ""}, "$set": { "rec.curStatus": "s:disabled" } }, False)

except Exception as e:
    print('runFMU: %s' % e, file=sys.stderr)
    
