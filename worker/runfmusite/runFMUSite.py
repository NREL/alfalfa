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
             a dictionary matching all IDs and display-names 
    '''
    dis_and_ID={}
    inputs_and_ID = {}
    outputs_and_ID = {}
    id_and_dis={}
    # default_input is a dictionay
    # with keys for every "_enable" input, set to value 0
    # in other words, disable everything
    default_input={}

    tag_data = get_tag_data(tag_filepath)

    for point in tag_data:
        var_name = point['dis'].replace('s:','')
        var_id = point['id'].replace('r:','')

        dis_and_ID[var_name] = var_id
        id_and_dis[var_id] = var_name
        
        if 'writable' in point.keys():
            inputs_and_ID[var_name] = var_id
            default_input[var_name.replace('_u', '_activate')] = 0;

        if 'writable' not in point.keys() and 'point' in point.keys():
            outputs_and_ID[var_name] = var_id
         
    return (dis_and_ID, inputs_and_ID, outputs_and_ID, id_and_dis, default_input)
        

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
        print(")))))) hey i am querying:(((((( ", mydoc)

    return mydoc
        
        
def check_vars(var):
   '''
   Purpose: print the var details to the terminal for debugging purpose
   Inputs:  variable 
   Returns: print statement on the terminal
   '''
   print(')))))) Hey i am checking var: '+ str(var) + '((((((: ', var)



####################   Entry for Main Program   #####################
############################################################################



try:
    if 'amazonaws' not in os.environ['S3_HOST']:
        s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url='http://minio:9000')
    else:
        s3 = boto3.resource('s3', region_name=os.environ['REGION'])

    #Initiate Mongo Database
    mongo_client = MongoClient(os.environ['MONGO_URL'])
    mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
    recs = mongodb.recs
    write_arrays = mongodb.writearrays

    # get arguments from calling program
    # which is the processMessage program
    site_ref = sys.argv[1]
    real_time_flag = sys.argv[2]
    time_scale = int(sys.argv[3])
    startTime = int(sys.argv[4])
    endTime = int(sys.argv[5])

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
    bucket = s3.Bucket(os.environ['S3_BUCKET'])
    bucket.download_file(key, tarpath)
    
    tar = tarfile.open(tarpath)
    tar.extractall(sim_path)
    tar.close()
    
    #get the tagging id, disp, etc......
    #tag_data = get_tag_data(tagpath)

    recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Running"}}, False)

    # Load fmu
    config = {
        'fmupath'  : fmupath,                
        'step'     : 60
    }

        
    (dis_and_id, tagid_and_inputs, tagid_and_outputs, id_and_dis, default_input) = \
            create_DisToID_dictionary(tagpath)
 

    #initiate the testcase
    tc = testcase.TestCase(config) 
    
    #run the FMU simulation
    kstep=0 
    stop = False
    simtime = 0
    while simtime < endTime and not stop:
        # u represents simulation input values
        u=default_input.copy()
        # look in the database for current write arrays
        # for each write array there is an array of controller
        # input values, the first element in the array with a value
        # is what should be applied to the simulation according to Project Haystack
        # convention
        for array in write_arrays.find({"siteRef": site_ref}):
            for val in array.get('val'):
                if val is not None:
                    _id = array.get('_id')
                    dis = id_and_dis.get(_id)
                    if dis:
                        u[dis] = val
                        u[dis.replace('_u', '_activate')] = 1
                        break

        y_output = tc.advance(u)
        simtime = tc.final_time
        output_time_string = 's:%s' %(simtime)
        recs.update_one( {"_id": site_ref}, { "$set": {"rec.datetime": output_time_string, "rec.simStatus":"s:Running"} } )

        # get each of the simulation output values and feed to the database
        for key in y_output.keys():
            value_y = y_output[key]
            
            if key!='time': 
                output_id = tagid_and_outputs[key]                          
                recs.update_one( {"_id": output_id }, {"$set": {"rec.curVal":"n:%s" %value_y, "rec.curStatus":"s:ok","rec.cur": "m:" }} )        

        time.sleep(5)

        # A client may have requested that the simulation stop early,
        # look for a signal to stop from the database
        site = recs.find_one({"_id": site_ref})
        if site and (site.get("rec",{}).get("simStatus") == "s:Stopping") :
            stop = True;
    
    # Clear all current values from the database when the simulation is no longer running
    recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}, "$unset": {"rec.datetime": ""} }, False)
    recs.update_many({"site_ref": site_ref, "rec.cur": "m:"}, {"$unset": {"rec.curVal": "", "rec.curErr": ""}, "$set": { "rec.curStatus": "s:disabled" } }, False)
    recs.update_many({"site_ref": site_ref, "rec.writable": "m:"}, {"$unset": {"rec.writeLevel": "","rec.writeVal": ""}, "$set": { "rec.writeStatus": "s:disabled" } }, False)

    shutil.rmtree(directory)

except Exception as e:
    print('runFMU: %s' % e, file=sys.stderr)
    
