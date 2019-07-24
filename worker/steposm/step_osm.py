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
import boto3
import tarfile
import shutil
import time
from pymongo import MongoClient
from parsevariables import Variables
import sys
import mlep
import subprocess
import logging
import re
import datetime
import pytz
import calendar
import traceback
import uuid
from dateutil.parser import parse
import math
import redis
from dateutil import parser

# Replace Date
def replace_idf_settings(idf_file, pattern, startDatetime, endDatetime, time_step):
    # Generate Lines
    begin_month_line = '  {},                                      !- Begin Month\n'.format(startDatetime.month)
    begin_day_line = '  {},                                      !- Begin Day of Month\n'.format(startDatetime.day)
    end_month_line = '  {},                                      !- End Month\n'.format(endDatetime.month)
    end_day_line = '  {},                                      !- End Day of Month\n'.format(endDatetime.day)
    time_step_line = '  {};                                      !- Number of Timesteps per Hour\n'.format(time_step)
    begin_year_line = '  {},                                   !- Begin Year\n'.format(startDatetime.year)
    end_year_line = '  {},                                   !- End Year\n'.format(endDatetime.year)
    dayOfweek_line = '  {},                                   !- Day of Week for Start Day\n'.format(startDatetime.strftime("%A"))
    
    # Overwrite File
    # the basic idea is to locate the pattern first (e.g. Timestep, RunPeriod)
    # then find the relavant lines by couting how many lines away from the patten.
    count = -1
    count_ts = 0
    with open(idf_file, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        for line in lines:
            count = count + 1             
            if pattern in line:
                #RunPeriod block
                line_runperiod = count
            if 'Timestep,' in line:
                line_timestep = count+1 
        
        for i, line in enumerate(lines):
            if (i<line_runperiod or i>line_runperiod+12) and (i != line_timestep) :
                f.write(line)
            elif i == line_timestep:
                line= time_step_line
                f.write(line)
            else:
               if i == line_runperiod + 2:
                  line = begin_month_line
               elif i == line_runperiod + 3:
                  line = begin_day_line
               elif i == line_runperiod + 4:
                  line = begin_year_line
               elif i == line_runperiod + 5:
                  line = end_month_line
               elif i == line_runperiod + 6:
                  line = end_day_line      
               elif i == line_runperiod + 7:
                  line = end_year_line
               elif i == line_runperiod + 8:
                  line = dayOfweek_line 
               else:
                  line = lines[i]
               f.write(line)

# Simulation Process Class
class SimProcess:
    # Simulation Status
    # sim_status = 0,1,2,3
    # 0 - Initialized
    # 1 - Running
    # 2 - Pause
    # 3 - Stopped

    def __init__(self):
        self.sim_status = 0             # 0=init, 1=running, 2=pause, 3=stop
        self.rt_step_time = 20          # Real-time step - seconds
        self.sim_step_per_hour = 60     # Simulation steps per hour, ************* it is fixed for both realtime and non-realtime simulation *************
        self.sim_step_time = 60.0   # Simulation time step - seconds
        self.start_time = 0             # Real-time step
        self.next_time = 0              # Real-time step
        self.start_date = '01/01'       # Start date for simulation (01/01)
        self.end_date = '12/31'         # End date for simulation (12/31)
        self.start_hour = 0             # Start hour for simulation (1-23)
        self.end_hour = 23              # End hour for simulation (1-23)
        self.start_minute = 0           # Start minute for simulation (0-59)
        self.end_minute = 0             # End minute for simulation (0-59)
        self.accept_timeout = 30000     # Accept timeout for simulation (ms)
        self.idf = None                 # EnergyPlus file path (/path/to/energyplus/file)
        self.mapping = None
        self.weather = None             # Weather file path (/path/to/weather/file)
        self.site_ref = None
        self.workflow_directory = None
        self.variables = None
        self.time_scale = 1
        self.real_time_flag = True

def get_energyplus_datetime(variables, outputs):
    month_index = variables.outputIndexFromTypeAndName("current_month","EMS")
    day_index = variables.outputIndexFromTypeAndName("current_day","EMS")
    hour_index = variables.outputIndexFromTypeAndName("current_hour","EMS")
    minute_index = variables.outputIndexFromTypeAndName("current_minute","EMS")
    
    day = int(round(outputs[ day_index ]))
    hour= int(round(outputs[ hour_index ]))
    minute= int(round(outputs[ minute_index ]))
    month = int(round(outputs[ month_index ]))
    year = sp.startDatetime.year

    if minute == 60 and hour == 23:
        hour = 0
        minute = 0
    elif minute == 60 and hour != 23:
        hour = hour + 1
        minute = 0

    return datetime.datetime(year, month, day, hour, minute)

def reset(tarinfo):
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = "root"
    return tarinfo

def finalize_simulation():
    # subprocess.call(['ReadVarsESO'])
    sim_id = str(uuid.uuid4())
    tar_name = "%s.tar.gz" % sim_id
    
    tar_file = tarfile.open(tar_name, "w:gz")
    tar_file.add(sp.workflow_directory, filter=reset, arcname=site_ref)
    tar_file.close()
    
    s3_key = "simulated/%s/%s" % (sp.site_ref,tar_name)
    bucket.upload_file(tar_name, s3_key)
    
    os.remove(tar_name)
    shutil.rmtree(sp.workflow_directory)

    site = recs.find_one({"_id": sp.site_ref})
    name = site.get("rec",{}).get("dis", "Unknown") if site else "Unknown"
    name = name.replace("s:","")
    time = str(datetime.datetime.now(tz=pytz.UTC))
    sims.insert_one({"_id": sim_id, "siteRef": sp.site_ref, "s3Key": s3_key, "name": name, "timeCompleted": time})
    recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}, "$unset": {"rec.datetime": "","rec.step": "" } }, False)
    recs.update_many({"_id": sp.site_ref, "rec.cur": "m:"}, {"$unset": {"rec.curVal": "", "rec.curErr": ""}, "$set": { "rec.curStatus": "s:disabled" } }, False)

def getInputs(bypass_flag):
    master_index = sp.variables.inputIndexFromVariableName("MasterEnable")
    if bypass_flag:
        ep.inputs[master_index] = 0
    else:
        ep.inputs = [0] * ((len(sp.variables.inputIds())) + 1)
        ep.inputs[master_index] = 1
        write_arrays = mongodb.writearrays
        for array in write_arrays.find({"siteRef": sp.site_ref}):
            for val in array.get('val'):
                if val:
                    index = sp.variables.inputIndex(array.get('_id'))
                    if index == -1:
                        logger.error('bad input index for: %s' % array.get('_id'))
                    else:
                        ep.inputs[index] = val
                        ep.inputs[index + 1] = 1
                        break
    # Convert to tuple
    inputs = tuple(ep.inputs)
    return inputs

##################################################################################
##############     The Entry for the Main section of runsite.py      #############
#########   The previous section contains all the functions to call  #############
##################################################################################

# Mongo Database
mongo_client = MongoClient(os.environ['MONGO_URL'])
mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
recs = mongodb.recs
sims = mongodb.sims

redis_client = redis.Redis(host=os.environ['REDIS_HOST'])
pubsub = redis_client.pubsub()

if len(sys.argv) == 7:
    print(sys.argv)

    site_ref = sys.argv[1]

    real_time_flag = (sys.argv[2] == 'true')

    time_scale = sys.argv[3]
    if time_scale == 'undefined':
        time_scale = 5
    else:
        time_scale = int(time_scale)

    if real_time_flag:
        time_scale = 1 

    year = datetime.datetime.today().year

    startDatetime = sys.argv[4]
    if startDatetime == 'undefined':
        startDatetime = datetime.datetime(year,1,1,0,0)
    else:
        startDatetime = parse(startDatetime, ignoretz=True)
        startDatetime = startDatetime.replace(second=0, microsecond=0)

    endDatetime = sys.argv[5]
    if endDatetime == 'undefined':
        endDatetime = datetime.datetime(year,12,31,23,59)
    else:
        endDatetime = parse(endDatetime, ignoretz=True)
        endDatetime = endDatetime.replace(second=0, microsecond=0)

    external_clock = (sys.argv[6] == 'true')

    if not real_time_flag:
        if startDatetime >= endDatetime:
            print('End time occurs on or before start time', file=sys.stderr)
            recs.update_one({"_id": site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}}, False)
            sys.exit(1)

else:
    print('runSimulation called with incorrect number of arguments: %s.' % len(sys.argv), file=sys.stderr)
    sys.exit(1)

if not site_ref:
    print('site_ref is empty', file=sys.stderr)
    sys.exit(1)

sim_path = '/simulate'
directory = os.path.join(sim_path, site_ref)

try:
    if not os.path.exists(directory):
        os.makedirs(directory)
except:
    sys.exit(1)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger('simulation')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log_file = os.path.join(directory, 'simulation.log')
fh = logging.FileHandler(log_file)
fh.setFormatter(formatter)
logger.addHandler(fh)

sqs = boto3.resource('sqs', region_name=os.environ['REGION'], endpoint_url=os.environ['JOB_QUEUE_URL'])
queue = sqs.Queue(url=os.environ['JOB_QUEUE_URL'])

s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])

sp = SimProcess()
ep = mlep.MlepProcess()

ep.bcvtbDir = '/root/bcvtb/'
ep.env = {'BCVTB_HOME': '/root/bcvtb'}

sp.site_ref = site_ref
sp.startDatetime = startDatetime
sp.endDatetime = endDatetime
sp.time_scale = time_scale
sp.real_time_flag = real_time_flag

tar_name = "%s.tar.gz" % sp.site_ref
key = "parsed/%s" % tar_name
tarpath = os.path.join(directory, tar_name)
osmpath = os.path.join(directory, 'workflow/run/in.osm')
sp.idf = os.path.join(directory, "workflow/run/%s" % sp.site_ref)
sp.weather = os.path.join(directory, 'workflow/files/weather.epw')
sp.mapping = os.path.join(directory, 'workflow/reports/haystack_report_mapping.json')
sp.workflow_directory = directory
variables_path = os.path.join(directory, 'workflow/reports/export_bcvtb_report_variables.cfg')
variables_new_path = os.path.join(directory, 'workflow/run/variables.cfg')

try:
    bucket = s3.Bucket(os.environ['S3_BUCKET'])
    bucket.download_file(key, tarpath)
    
    tar = tarfile.open(tarpath)
    tar.extractall(sim_path)
    tar.close()
    
    sp.variables = Variables(variables_path, sp.mapping)
    
    subprocess.call(['openstudio', 'steposm/translate_osm.rb', osmpath, sp.idf])
    shutil.copyfile(variables_path, variables_new_path)
    
    ## Simulation Parameters
    replace_idf_settings(sp.idf + '.idf', 'RunPeriod,', sp.startDatetime, sp.endDatetime, sp.sim_step_per_hour)
    
    # Arguments
    ep.accept_timeout = sp.accept_timeout
    ep.mapping = sp.mapping
    ep.flag = 0
    
    # Parse directory
    idf_file_details = os.path.split(sp.idf)
    ep.workDir = idf_file_details[0]
    ep.arguments = (sp.idf, sp.weather)
    
    # Initialize input tuplet
    ep.inputs = [0] * ((len(sp.variables.inputIds())) + 1)
    
    # Start EnergyPlus co-simulation
    (ep.status, ep.msg) = ep.start()
    
    # Check E+
    if ep.status != 0:
        logger.error('Could not start EnergyPlus: %s.' % ep.msg)
        ep.flag = 1
    
    # Accept Socket
    [ep.status, ep.msg] = ep.accept_socket()
    
    if ep.status != 0:
        logger.error('Could not connect EnergyPlus: %s.' % ep.msg)
        ep.flag = 1
    
    # The main simulation loop
    ep.deltaT = sp.sim_step_time    # time step - sec
    ep.kStep = 1                    # current simulation step
    bypass_flag = True
    
    # Simulation Status
    if ep.is_running == True:
        sp.sim_status = 1
    
    # Set next step
    next_t = datetime.datetime.now().timestamp() 

    # only used for external_clock
    advance = False
    if external_clock:
        pubsub.subscribe(sp.site_ref)
     
    recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Starting"}}, False)
    real_time_step=0 

    while True:
        stop = False;
        t = datetime.datetime.now().timestamp()

        if external_clock:
            message = pubsub.get_message()
            if message:
                data = message['data']
                if data == b'advance':
                    advance = True
                elif data == b'stop':
                    stop = True
            
        # Iterating over timesteps
        if ( ep.is_running and (sp.sim_status == 1) and (not stop) and t >= next_t and (not external_clock) ) or \
           ( (ep.is_running and (sp.sim_status == 1) and (not stop) and bypass_flag) ) or \
           ( ep.is_running and (sp.sim_status == 1) and (not stop) and (not bypass_flag) and external_clock and advance ):

            # Check for "Stopping" here so we don't hit the database as fast as the event loop will run
            # Instead we only check the database for stopping at each simulation step
            rec = recs.find_one({"_id": sp.site_ref})
            if rec and (rec.get("rec",{}).get("simStatus") == "s:Stopping") :
                stop = True;
                
            if stop == False:
                # Write user inputs to E+
                inputs = getInputs(bypass_flag)
                ep.write(mlep.mlep_encode_real_data(2, 0, (ep.kStep - 1) * ep.deltaT, inputs))

                # Read outputs
                packet = ep.read()
                [ep.flag, eptime, outputs] = mlep.mlep_decode_packet(packet)
                ep.outputs = outputs
                energyplus_datetime = get_energyplus_datetime(sp.variables, outputs)
                ep.kStep = ep.kStep + 1

                if energyplus_datetime >= sp.startDatetime:  
                    bypass_flag = False  # Stop bypass
                    redis_client.hset(site_ref, 'control', 'idle')
            
                if bypass_flag == False:
                    for output_id in sp.variables.outputIds():
                        output_index = sp.variables.outputIndex(output_id)
                        if output_index == -1:
                            logger.error('bad output index for: %s' % output_id)
                        else:
                            output_value = ep.outputs[output_index]
                            
                            # TODO: Make this better with a bulk update
                            # Also at some point consider removing curVal and related fields after sim ends
                            recs.update_one({"_id": output_id}, {
                                "$set": {"rec.curVal": "n:%s" % output_value, "rec.curStatus": "s:ok", "rec.cur": "m:"}}, False)
    
                    real_time_step = real_time_step + 1
                    output_time_string = "s:%s" % energyplus_datetime.isoformat()
                    recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.datetime": output_time_string, "rec.step": "n:" + str(real_time_step), "rec.simStatus": "s:Running"}}, False)
    
                    # Advance time
                    next_t = next_t + sp.sim_step_time / sp.time_scale

                # Check Stop
                if ( ep.is_running == True and (energyplus_datetime > sp.endDatetime) ) :
                    stop = True
                elif ( sp.sim_status == 3 and ep.is_running == True ) :
                    stop = True

                if external_clock and not bypass_flag:
                    advance = False
                    redis_client.publish(sp.site_ref, 'complete')
                    redis_client.hset(site_ref, 'control', 'idle')
    
        if stop:
            finalize_simulation()
            ep.stop(True)      
            ep.is_running = 0
            sp.sim_status = 0
            break

except:
    logger.error("Simulation error: %s", sys.exc_info()[0])
    traceback.print_exc()
    finalize_simulation()

