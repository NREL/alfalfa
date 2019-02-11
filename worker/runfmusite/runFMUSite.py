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
import testcase
import json


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
        #print(" )))))) Hey tag data are: (((((( ",tag_data)

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
        print (')))))): var-name: ', var_name)
        var_id   = point['id']
        dis_and_ID[var_name] = var_id
        
        if 'input' in var_name:
            #clean the var-name, discarding: ':input','s:','r:'
            input_var = var_name.replace(':input','')
            input_var = input_var.replace('s:','')
            inputs_and_ID[input_var] = var_id.replace('r:','')

        if 'output' in var_name:
            #clean the var-name, discarding: ':output','s:','r:'
            output_var = var_name.replace(':output','')
            output_var = output_var.replace('s:','')
            outputs_and_ID[output_var] = var_id.replace('r:','')
         
    return (dis_and_ID, inputs_and_ID, outputs_and_ID)
        

def query_var_byID(database, var_id):
    '''
    Purpose: query a variable by ID to the database
    Inputs:  database, and the id of the variable
    Returns: the details of the data
    '''
    myquery = {"_id": data_id}
    mydoc = database.find(myquery)
    for x in mydoc:
        print(")))))) hey i am querying:(((((( ", x)
        
def check_vars(var):
   '''
   Purpose: print the var details to the terminal for debugging purpose
   Inputs:  variable 
   Returns: print statement on the terminal
   '''
   print(')))))) Hey i am checking '+ str(var) + '((((((: ', var)



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
    u={}
    for each_input in tc.get_inputs():
        if each_input !='time':
            u[each_input]=1.0   
 
    #run the FMU simulation
    kstep=0 
    #while tc.start_time <= 1000000000000:
    for i in range(10):
        time.sleep(5)
        tc.advance(u)
        output = tc.get_results()
        
        u_output = output['u']
        y_output = output['y']
        for key in u_output.keys():
            value_u = u_output[key]
            
            if key!='time':
                input_id = tagid_and_inputs[key]
                                
                cur_value = 3.33
                recs.update_one( {"_id": input_id }, {"$set": {"rec.curVal":"n:%s" %cur_value, "rec.curStatus":"s:ok","rec.cur": "m:" }} )

        for key in y_output.keys():
            value_y = y_output[key]
            
            if key!='time': 
                output_id = tagid_and_outputs[key]
                             
                cur_value =273.15
                recs.update_one( {"_id": output_id }, {"$set": {"rec.curVal":"n:%s" %cur_value, "rec.curStatus":"s:ok","rec.cur": "m:" }} )        
             
        

    #shutil.rmtree(directory)
    
    recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}, "$unset": {"rec.datetime": ""} }, False)
    recs.update_many({"_id": site_ref, "rec.cur": "m:"}, {"$unset": {"rec.curVal": "", "rec.curErr": ""}, "$set": { "rec.curStatus": "s:disabled" } }, False)

except Exception as e:
    print('runFMU: %s' % e, file=sys.stderr)

