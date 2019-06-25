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

import os
import boto3
import tarfile
import shutil
import time
import sys
import json
import redis
from pymongo import MongoClient
import common
import common.testcase

class RunFMUSite:
    def __init__(self, **kwargs):
        self.s3 = boto3.resource('s3', region_name='us-east-1', endpoint_url=os.environ['S3_URL'])
        self.redis = redis.Redis(host=os.environ['REDIS_HOST'])
        self.pubsub = self.redis.pubsub()

        #Initiate Mongo Database
        mongo_client = MongoClient(os.environ['MONGO_URL'])
        self.mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
        self.recs = self.mongodb.recs
        self.write_arrays = self.mongodb.writearrays

        # get arguments from calling program
        # which is the processMessage program
        self.site_ref = kwargs['site_ref']
        self.real_time_flag = kwargs['real_time_flag']
        self.time_scale = kwargs['time_scale']
        self.startTime = kwargs['startTime']
        self.endTime = kwargs['endTime']
        self.externalClock = kwargs['externalClock']

        #build the path for zipped-file, fmu, json
        sim_path = '/simulate'
        self.directory = os.path.join(sim_path, self.site_ref)
        tar_name = "%s.tar.gz" % self.site_ref
        key = "parsed/%s" % tar_name
        tarpath = os.path.join(self.directory, tar_name)
        fmupath = os.path.join(self.directory, 'model.fmu')
        tagpath = os.path.join(self.directory, 'tags.json')

        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        
        #download the tar file and tag file
        bucket = self.s3.Bucket('alfalfa')
        bucket.download_file(key, tarpath)
        
        tar = tarfile.open(tarpath)
        tar.extractall(sim_path)
        tar.close()

        # Load fmu
        config = {
            'fmupath'  : fmupath,                
            'step'     : 60
        }
            
        (self.tagid_and_outputs, self.id_and_dis, self.default_input) = self.create_tag_dictionaries(tagpath)
 
        #initiate the testcase
        self.tc = common.testcase.TestCase(config) 
        
        #run the FMU simulation
        self.kstep=0 
        self.stop = False
        self.simtime = 0

        if self.externalClock:
            self.pubsub.subscribe(self.site_ref)

    def create_tag_dictionaries(self, tag_filepath):
        '''
        Purpose: matching the haystack display-name and IDs
        Inputs:  a json file containing all the tagged data
        Returns: a dictionary matching all outputs and IDs 
                 a dictionary matching all IDs and display-names 
                 a dictionary for every _enable input, set to value 0
        '''
        outputs_and_ID = {}
        id_and_dis={}
        # default_input is a dictionay
        # with keys for every "_enable" input, set to value 0
        # in other words, disable everything
        default_input={}
    
        # Get Haystack tag data, from tag_filepath
        tag_data = {}
        with open( tag_filepath ) as json_data:
            tag_data = json.load(json_data)
    
        for point in tag_data:
            var_name = point['dis'].replace('s:','')
            var_id = point['id'].replace('r:','')
    
            id_and_dis[var_id] = var_name
            
            if 'writable' in point.keys():
                default_input[var_name.replace('_u', '_activate')] = 0
    
            if 'writable' not in point.keys() and 'point' in point.keys():
                outputs_and_ID[var_name] = var_id
             
        return (outputs_and_ID, id_and_dis, default_input)

    def run(self):
        self.init_sim_status()

        if self.externalClock:
            while True:
                message = self.pubsub.get_message()
                if message:
                    data = message['data']
                    if data == 'advance':
                        self.step()
                        self.redis.publish(self.site_ref, 'complete')
                        self.set_idle_state()
                    elif data == 'stop':
                        self.set_idle_state()
                        break;
        else:
            while self.simtime < self.endTime:
                if self.db_stop_set():
                    break;
                self.step()
                # TODO: Make this respect time scale provided by user
                time.sleep(5)

        self.cleanup()

    # Check the database for a stop signal
    # and return true if stop is requested
    def db_stop_set(self): 
        # A client may have requested that the simulation stop early,
        # look for a signal to stop from the database
        site = self.recs.find_one({"_id": self.site_ref})
        if site and (site.get("rec",{}).get("simStatus") == "s:Stopping") :
            self.stop = True
        return self.stop

    # cleanup after the simulation is stopped
    def cleanup(self):
        # Clear all current values from the database when the simulation is no longer running
        self.recs.update_one({"_id": self.site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}, "$unset": {"rec.datetime": ""} }, False)
        self.recs.update_many({"site_ref": self.site_ref, "rec.cur": "m:"}, {"$unset": {"rec.curVal": "", "rec.curErr": ""}, "$set": { "rec.curStatus": "s:disabled" } }, False)
        self.recs.update_many({"site_ref": self.site_ref, "rec.writable": "m:"}, {"$unset": {"rec.writeLevel": "","rec.writeVal": ""}, "$set": { "rec.writeStatus": "s:disabled" } }, False)

        shutil.rmtree(self.directory)

    def set_idle_state(self):
        self.redis.hset(site_ref, 'control', 'idle')

    def init_sim_status(self):
        self.set_idle_state()
        output_time_string = 's:%s' %(self.simtime)
        self.recs.update_one( {"_id": self.site_ref}, { "$set": {"rec.datetime": output_time_string, "rec.simStatus":"s:Running"} } )

    def update_sim_status(self):
        self.simtime = self.tc.final_time
        output_time_string = 's:%s' %(self.simtime)
        self.recs.update_one( {"_id": self.site_ref}, { "$set": {"rec.datetime": output_time_string, "rec.simStatus":"s:Running"} } )
        
    def step(self):
        # u represents simulation input values
        u=self.default_input.copy()
        # look in the database for current write arrays
        # for each write array there is an array of controller
        # input values, the first element in the array with a value
        # is what should be applied to the simulation according to Project Haystack
        # convention
        for array in self.write_arrays.find({"siteRef": self.site_ref}):
            _id = array.get('_id')
            for val in array.get('val'):
                if val is not None:
                    dis = self.id_and_dis.get(_id)
                    if dis:
                        u[dis] = val
                        u[dis.replace('_u', '_activate')] = 1
                        break
        
        y_output = self.tc.advance(u)
        self.update_sim_status()
        
        # get each of the simulation output values and feed to the database
        for key in y_output.keys():
            if key!='time': 
                output_id = self.tagid_and_outputs[key]                          
                value_y = y_output[key]
                self.recs.update_one( {"_id": output_id }, {"$set": {"rec.curVal":"n:%s" %value_y, "rec.curStatus":"s:ok","rec.cur": "m:" }} )        

####################   Entry for Main Program   #####################
############################################################################

# get arguments from calling program
# which is the processMessage program

site_ref = sys.argv[1]
real_time_flag = (sys.argv[2] == 'true')
time_scale = sys.argv[3]
if time_scale == 'undefined':
    time_scale = 5
else:
    time_scale = int(time_scale)
if real_time_flag:
    time_scale = 1 
startTime = sys.argv[4]
if startTime == 'undefined':
    startTime = 0;
else:
    starTime = int(sys.argv[4])
endTime = sys.argv[5]
if endTime == 'undefined':
    endTime = 86400;
else:
    endTime = int(sys.argv[5])
externalClock = (sys.argv[6] == 'true')

runFMUSite = RunFMUSite(site_ref=site_ref, real_time_flag=real_time_flag, time_scale=time_scale, startTime=startTime, endTime=endTime, externalClock=externalClock)
runFMUSite.run()
    
