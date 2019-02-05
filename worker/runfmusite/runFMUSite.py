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
    '''this function will retrieve the tagged data,
     which are model-exchange variables in FMU. 
     This function will get the tagged properties, like id, dis. etc...
    '''
    with open( tag_filepath ) as json_data:
        tag_data = json.load(json_data)
        #print(" )))))) Hey tag data are: (((((( ",tag_data)

    return tag_data


def match_tags_fmu_vars(tag_data, input_names, output_names):
    '''This function will match the tags with the FMU variables:
        inputs and outputs.
       It will return a dict containing the id and variable names
    '''
    #for input_var in input_names:
    tagid_and_inputs={}
    for x in tag_data:
        key_list= x.keys()
        for each_key in key_list:
            for input_var in input_names:
                if input_var in x[each_key]:
                    tagid_and_inputs[input_var]=x[u'id']
    #print("hey input id-vars ))))))((((((: ", tagid_and_inputs)

    tagid_and_outputs={}
    for x in tag_data:
        key_list= x.keys()
        for each_key in key_list:
            for output_var in output_names:
                if output_var in x[each_key]:
                    tagid_and_outputs[output_var]=x[u'id']
    #print("hey output  id-vars ))))))((((((: ", tagid_and_outputs)

    return (tagid_and_inputs, tagid_and_outputs)


############################################################################
####################   Entry for Main Program   #####################
############################################################################



try:
    s3 = boto3.resource('s3', region_name='us-east-1', endpoint_url=os.environ['S3_URL'])

    # Mongo Database
    mongo_client = MongoClient(os.environ['MONGO_URL'])
    mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
    recs = mongodb.recs

    site_ref = sys.argv[1]
    real_time_flag = sys.argv[2]
    time_scale = int(sys.argv[3])
    user_start_Datetime = parse(sys.argv[4])
    user_end_Datetime = parse(sys.argv[5])

    sim_path = '/simulate'
    directory = os.path.join(sim_path, site_ref)
    tar_name = "%s.tar.gz" % site_ref
    key = "parsed/%s" % tar_name
    tarpath = os.path.join(directory, tar_name)
    fmupath = os.path.join(directory, 'model.fmu')
    tagpath = os.path.join(directory, 'tags.json')

    
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    bucket = s3.Bucket('alfalfa')
    bucket.download_file(key, tarpath)
    bucket.download_file(key, tagpath)
    
    tar = tarfile.open(tarpath)
    tar.extractall(sim_path)
    tar.close()
    
    #get the tagging id, disp, etc......
    tag_data = get_tag_data(tagpath)

    recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Running"}}, False)

    myquery = {"_id": site_ref}
    mydoc = recs.find(myquery)
    for x in mydoc:
        #print(")))))) hey i am querying:(((((( ",x)
        pass

    # Load fmu
    config = {
        'fmupath'  : fmupath,                
        'step'     : 60
    }

    tc = testcase.TestCase(config)   
    input_names  = tc.get_inputs()
    output_names = tc.get_measurements()
    #print(")))))) output names: ((((((", output_names)
  
    (tagid_and_inputs, tagid_and_outputs) = \
            match_tags_fmu_vars(tag_data, input_names, output_names)
    ''' 
    for varname in tagid_and_inputs.keys():
        input_id = tagid_and_inputs[varname]
        print("))) key (((:", varname, " $$$ value $$$ :", input_id )
        input_id = input_id.replace('r:','')
        recs.insert_one ( {"_id": input_id }, {"$set": {"rec.curVal":"n:", "rec.curStatus":"s:ok","rec.cur": "m:" }} )
 
    for varname in tagid_and_outputs.keys():
        output_id = tagid_and_outputs[varname]
        print("))) key (((:", varname, " $$$ value $$$ :", output_id )
        output_id = output_id.replace('r:','')
        #recs.insert_one( { "fakeid": output_id, "name": varname }  )
        recs.insert_one( {"_id": output_id }, {"$set": {"rec.curVal":"", "rec.curStatus":"s:ok","rec.cur": "m:" }} )
    '''
 
    
    #setup the fake inputs
    u={}
    for each_input in input_names:
        if each_input !='time':
            u[each_input]=1.0   
 

    kstep=0 
    #while tc.start_time <= 1000000000000:
    for i in range(10):
        print("))))))))))) step counter: ((((((((((( ", i)
        time.sleep(5)
        tc.advance(u)
        output = tc.get_results()
        #print ("hey output y: ", output['y'])
        #print ("hey output u: ", output['u'])
        u_output = output['u']
        y_output = output['y']
        for key in u_output.keys():
            value_u = u_output[key]
            #print(")))))) key/value u is: ((((((", key, value_u )
            if key!='time':
                input_id = tagid_and_inputs[key]
                print (")))))) Hey input id: ((((((", input_id)
                #input_id = input_id.replace("r:","")
                recs.update_one( {"_id": input_id }, {"$set": {"rec.curVal":"n:%s" %value_u, "rec.curStatus":"s:ok","rec.cur": "m:" }} )

        for key in y_output.keys():
            value_y = y_output[key]
            #print(")))))) key/value y is: ((((((", key, value_y )
            if key!='time': 
                output_id = tagid_and_outputs[key]
                #output_id = output_id.replace("r:","")
                print (")))))) Hey output id: ((((((", output_id)
                #print("outputid: ))))))((((((:", output_id)
                recs.update_one( {"_id": output_id }, {"$set": {"rec.curVal":"n:%s" %value_y, "rec.curStatus":"s:ok","rec.cur": "m:" }} )        
             
        for varname in tagid_and_outputs.keys():
            output_id = tagid_and_outputs[varname]
            print(" )))))) hey querying output_id: (((((( ", output_id )
            myquery = { "_id": output_id }
            mydoc = recs.find(myquery)
            for x in mydoc:
                print(")))))) my query is: (((((( ", x)

    #shutil.rmtree(directory)
    
    recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}, "$unset": {"rec.datetime": ""} }, False)
    #recs.update_many({"_id": site_ref, "rec.cur": "m:"}, {"$unset": {"rec.curVal": "", "rec.curErr": ""}, "$set": { "rec.curStatus": "s:disabled" } }, False)

except Exception as e:
    print('runFMU: %s' % e, file=sys.stderr)

