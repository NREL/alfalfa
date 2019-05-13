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
from datetime import date, datetime, timedelta, timezone
import pytz
import calendar
import traceback
import uuid
from dateutil.parser import parse
import math
from dateutil import parser


# Time Zone
def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


# Replace Date
def replace_idf_settings(idf_file, pattern, date_start, date_end, time_step, year_start, year_end, dayOfweek):
    # Parse Date
    begin_month = [int(s) for s in re.findall(r'\d+', date_start)][0]
    begin_day = [int(s) for s in re.findall(r'\d+', date_start)][1]
    end_month = [int(s) for s in re.findall(r'\d+', date_end)][0]
    end_day = [int(s) for s in re.findall(r'\d+', date_end)][1]
    dates = (begin_month, begin_day, end_month, end_day)
    print("*** debugging the actual dates here: ***", dates)
    # Generate Lines
    begin_month_line = '  {},                                      !- Begin Month\n'.format(begin_month)
    begin_day_line = '  {},                                      !- Begin Day of Month\n'.format(begin_day)
    end_month_line = '  {},                                      !- End Month\n'.format(end_month)
    end_day_line = '  {},                                      !- End Day of Month\n'.format(end_day)
    time_step_line = '  {};                                      !- Number of Timesteps per Hour\n'.format(time_step)
    begin_year_line = '  {},                                   !- Begin Year\n'.format(year_start)
    end_year_line = '  {},                                   !- End Year\n'.format(year_end)
    dayOfweek_line = '  {},                                   !- Day of Week for Start Day\n'.format(dayOfweek)
    
    # Overwrite File
    # the basic idea is to locate the pattern first (e.g. Timestep, RunPeriod)
    # then find the relavant lines by couting how many lines away from the patten.
    count = -1
    count_ts = 0
    with open(idf_file, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        #print("*** debugging: i am checking here!!! ")
        for line in lines:
            count = count + 1             
            if pattern in line:
                #RunPeriod block
                line_runperiod = count
                print("*** degugging for the runperiod *** ", line_runperiod)
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
           
   
        
    return dates


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
        self.sim_step_time = 60/self.sim_step_per_hour*60   # Simulation time step - seconds
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
    
    #subprocess.call(['ReadVarsESO'])
    
    s3_key = "simulated/%s/%s" % (sp.site_ref,tar_name)
    bucket.upload_file(tar_name, s3_key)
    
    os.remove(tar_name)
    shutil.rmtree(sp.workflow_directory)

    site = recs.find_one({"_id": sp.site_ref})
    name = site.get("rec",{}).get("dis", "Unknown") if site else "Unknown"
    name = name.replace("s:","")
    time = str(datetime.now(tz=pytz.UTC))
    sims.insert_one({"_id": sim_id, "siteRef": sp.site_ref, "s3Key": s3_key, "name": name, "timeCompleted": time})
    recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}, "$unset": {"rec.datetime": "","rec.step": "" } }, False)
    recs.update_many({"_id": sp.site_ref, "rec.cur": "m:"}, {"$unset": {"rec.curVal": "", "rec.curErr": ""}, "$set": { "rec.curStatus": "s:disabled" } }, False)
    #sys.exit()


def check_local_timezone():
    #check the UTC time zone
    print("****** Yanfei: time zone: ", time.tzname)


def utc_to_local_datetime(utc_dt, time_zone):
    '''
    This function will convert the UTC-datetime coming from user to local-datetime
    '''
    local = utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=pytz.timezone('US/Mountain'))
    return local

def utc_to_unix_datetime(utc_dt):
    '''This function will convert the utc-datetime to unix-datetime'''
    return utc_dt.timestamp()


def check_localtime(user_start_datetime, user_end_datetime, time_zone):
    '''The user_start_datetime and user_end_datetime are from the user picks at the front end; '''
    '''The user_start_datetime and user_end_datetime are local time at the front end;'''
    '''However the backend transferred the user selected time to UTC format'''
    '''We have to convert the UTC-datetime to local-datetime'''
    
    # check the user input time_zone
    timezone_list_US = ['US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific', 'US/Alaska', 'US/Hawaii'] 
    if time_zone not in timezone_list_US:
        print ("Please change your input time-zone into one of the list: ", timezone_list_US)
        #sys.exit()
     
    #obtain the UTC time first
    datetime_utcnow = datetime.utcnow()
    #print("****** Yanfei: datetime--utcnow: ", str(datetime_utcnow) )
   
    
    #obtain the local timeie from user; here use Denver as a demo      
    start_datetime = utc_to_local_datetime(user_start_datetime, time_zone)
    end_datetime   = utc_to_local_datetime(user_end_datetime, time_zone)
 
    #obtain the year, applied to EnergyPlus version >9.0.0
    year_start = int ( str(start_datetime)[0:4] )   
    year_end   = int ( str(  end_datetime)[0:4] ) 

    #obtain the day_of_week
    # this parameter will be input to EnergyPlus verison>9.0.0
    # this will make the real simulation starting at the correct day of week
    day_of_week = start_datetime.weekday()
    if day_of_week==0:
        dayOFweek="Monday"
    elif day_of_week==1:
        dayOFweek="Tuesday"    
    elif day_of_week==2:
        dayOFweek="Wednesday"
        print("****** Yanfei: day of week:****** ", dayOFweek)
    elif day_of_week==3:
        dayOFweek="Thursday"
    elif day_of_week==4:
        dayOFweek="Friday"
    elif day_of_week==5:
        dayOFweek="Saturday"
    else:
        dayOFweek="Sunday"

    return (start_datetime, end_datetime, dayOFweek, year_start, year_end)


def get_current_datetime_ep(ep_year, ep_month, ep_day, ep_hour, ep_minute, local_time_zone):
    '''Purpose: obtain the EP time outputs and parse it into DateTime object'''
    if int(ep_minute) == 60 and int(ep_hour)==23:
        ep_hour=0
        ep_minute = 0
    elif int(ep_minute) == 60 and int(ep_hour)!=23:
        ep_hour = ep_hour +1
        ep_minute = 0
    else:
        pass
        
    current_datetime_ep = datetime(int(ep_year), int(ep_month), int(ep_day), int(ep_hour), int(ep_minute), tzinfo=pytz.timezone(local_time_zone) )
    
    return current_datetime_ep



##################################################################################
##############     The Entry for the Main section of runsite.py      #############
#########   The previous section contains all the functions to call  #############
##################################################################################
#startDatetime = datetime.today()

# Mongo Database
mongo_client = MongoClient(os.environ['MONGO_URL'])
mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
recs = mongodb.recs
sims = mongodb.sims

if len(sys.argv) == 6:
    site_ref = sys.argv[1]
    real_time_flag = sys.argv[2]
    time_scale = int(sys.argv[3])
    if real_time_flag !='false':
        time_scale =1 
       
    
    user_start_Datetime = parse(sys.argv[4])
    user_end_Datetime = parse(sys.argv[5])
      

    local_time_zone = 'US/Mountain'
   
    (startDatetime, endDatetime, dayOfweek, year_start, year_end) = check_localtime(user_start_Datetime, user_end_Datetime, local_time_zone)
     
    start_time_unix = utc_to_unix_datetime(user_start_Datetime)
    end_time_unix   = utc_to_unix_datetime(user_end_Datetime)
 
    start_date = "%02d/%02d" % (startDatetime.month,startDatetime.day)
    start_day = "%02d" % (startDatetime.day)
    start_hour = startDatetime.hour
    start_minute = startDatetime.minute

    end_date = "%02d/%02d" % (endDatetime.month,endDatetime.day)
    end_hour = endDatetime.hour
    end_minute = endDatetime.minute    

    # time_zone = sys.argv[8]
    # time_zone = 'America/Denver'
    # sim_step_per_hour = sys.argv[9]

    if real_time_flag == 'false':
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
    print('error making simulation directory for site_ref: %s' % site_ref, file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger('simulation')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log_file = os.path.join(directory, 'simulation.log')
fh = logging.FileHandler(log_file)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)


sqs = boto3.resource('sqs', region_name=os.environ['REGION'], endpoint_url=os.environ['JOB_QUEUE_URL'])
queue = sqs.Queue(url=os.environ['JOB_QUEUE_URL'])

s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])

sp = SimProcess()
ep = mlep.MlepProcess()

ep.bcvtbDir = '/root/bcvtb/'
ep.env = {'BCVTB_HOME': '/root/bcvtb'}

sp.start_date = start_date
sp.end_date = end_date
sp.start_hour = start_hour
sp.end_hour = end_hour
sp.start_minute = start_minute
sp.end_minute = end_minute
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
    
    subprocess.call(['openstudio', 'runsite/translate_osm.rb', osmpath, sp.idf])
    shutil.copyfile(variables_path, variables_new_path)
    
    
    # Simulation Parameters
    #sp.sim_step_time = 60 / sp.sim_step_per_hour * 60  # Simulation time step - seconds
    bypass_flag = True
    sim_date = replace_idf_settings(sp.idf + '.idf', 'RunPeriod,', sp.start_date, sp.end_date, sp.sim_step_per_hour, year_start, year_end, dayOfweek)
    
    
    try:
        sp.rt_step_time = sp.sim_step_time / sp.time_scale   # Seconds
    except:
        sp.rt_step_time = 10                                    # Seconds
        print("Note: the coupling of simulation might take some time for reading and writing, thus the minimum real-time step is 10 seconds")
    
     
    logger.info('########################################################################')
    logger.info('######################## INPUT VARIABLES ###############################')
    logger.info('########################################################################')
    logger.info('sp.start_date: %s' % sp.start_date)
    logger.info('sp.end_date: %s' % sp.end_date)
    logger.info('sp.start_hour: %s' % sp.start_hour)
    logger.info('sp.end_hour: %s' % sp.end_hour)
    logger.info('sp.start_minute: %s' % sp.start_minute)
    logger.info('sp.end_minute: %s' % sp.end_minute)
    logger.info('sp.sim_step_time: %s' % sp.sim_step_time)
    logger.info('sp.rt_step_time: %s' % sp.rt_step_time)
    logger.info('sp.real_time_flag: %s' % sp.real_time_flag)
    logger.info('sp.time_scale: %s' % sp.time_scale)
    logger.info('sp.startDatetime: %s' % sp.startDatetime)
    logger.info('sp.endDatetime: %s' % sp.endDatetime)
    logger.info('sp.start_minute: %s' % sp.start_minute)
    logger.info('sp.end_minute: %s' % sp.end_minute)
    
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
    else:
        logger.info('EnergyPlus Started')
    
    # Accept Socket
    [ep.status, ep.msg] = ep.accept_socket()
    
    if ep.status != 0:
        logger.error('Could not connect EnergyPlus: %s.' % ep.msg)
        ep.flag = 1
    
    # The main simulation loop
    ep.deltaT = sp.sim_step_time    # time step - sec
    ep.kStep = 1                    # current simulation step
    # Days
    d0 = date(year_start, sim_date[0], sim_date[1])
    d1 = date(year_end,   sim_date[2], sim_date[3])
    
    
    delta = d1 - d0
    ep.MAX_STEPS = (24 * delta.days + sp.end_hour) * sp.sim_step_per_hour + sp.end_minute + 1# Max. Number of Steps
    
    
    logger.info('############# MAX STEPS:  {0} #############'.format(ep.MAX_STEPS))
    logger.info('############# Days:       {0} #############'.format(delta.days))
    logger.info('############# End Hour :  {0} #############'.format(sp.end_hour))
    logger.info('############# End Minute: {0} #############'.format(sp.end_minute))
    logger.info('############# Step/Hour:  {0} #############'.format(sp.sim_step_per_hour))
    logger.info('############# Start Hour: {0} #############'.format(sp.start_hour))
    
    # Simulation Status
    if ep.is_running == True:
        sp.sim_status = 1
    
    # Set next step
    utc_time = datetime.now(tz=pytz.UTC)
    #t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone('US/Mountain'))
    t = utc_time.timestamp()
    next_t = t
     
    recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Starting"}}, False)
    real_time_step=0 
    # probably need some kind of fail safe/timeout to ensure
    # that this is not an infinite loop
    # or maybe a timeout in the python call to this script
    while True:
        stop = False;
    
        #sp.next_time = time.time()
        utc_time = datetime.now(tz=pytz.UTC)
        #t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(local_time_zone))
        t = utc_time.timestamp()

        local_time = utc_to_local_datetime(utc_time, local_time_zone)
        output_time_string = 't:%s %s' % (local_time.isoformat(), local_time.tzname())
         
            
        # Iterating over timesteps
        #   if (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and (sp.next_time - sp.start_time >= sp.rt_step_time)) or\
        if (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and t >= next_t) or\
                (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and bypass_flag):  # Bypass Time
        #if (ep.is_running and (sp.sim_status == 1) and (t <= end_time_unix ) and t >= next_t) or\
        #        (ep.is_running and (sp.sim_status == 1) and (t <= end_time_unix) and bypass_flag):  # Bypass Time

            #logger.info('E+ Running: {0}, Sim Status: {1}, E+ Step: {2}, Elapsed step time: {3}, RT Step Time: {4}'.format(
            #    ep.is_running, sp.sim_status, ep.kStep, sp.next_time - sp.start_time, sp.rt_step_time))
            #logger.info('###### t: {0}'.format(t))
            try:
                # Check for "Stopping" here so we don't hit the database as fast as the event loop will run
                # Instead we only check the database for stopping at each simulation step
                rec = recs.find_one({"_id": sp.site_ref})
                if rec and (rec.get("rec",{}).get("simStatus") == "s:Stopping") :
                    logger.info("Stopping")
                    stop = True;
                    
                if stop == False:
                    
                    # Read packet
                    # Get current time
                    #utc_time = datetime.now(tz=pytz.UTC)
                    #next_t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(time_zone)) + \
                    #         timedelta(seconds=sp.rt_step_time)
                    packet = ep.read()
                    # logger.info('Packet: {0}'.format(packet))
                    if packet == '':
                        raise mlep.InputError('packet', 'Message Empty: %s.' % ep.msg)

                    # Parse it to obtain building outputs
                    [ep.flag, eptime, outputs] = mlep.mlep_decode_packet(packet)
                    # Log Output Data
                    ep.outputs = outputs
                    #print("***Yanfei Checking Outputs coming from EnergyPlus*** ", outputs)

                    variables = Variables(variables_new_path, sp.mapping)
                    month_index = variables.outputIndexFromTypeAndName("current_month","EMS")
                    day_index = variables.outputIndexFromTypeAndName("current_day","EMS")
                    hour_index = variables.outputIndexFromTypeAndName("current_hour","EMS")
                    minute_index = variables.outputIndexFromTypeAndName("current_minute","EMS")


                    ep_current_day = outputs[ day_index ]
                    ep_current_hour= outputs[ hour_index ]
                    ep_current_minute= outputs[ minute_index ]
                    ep_current_month = outputs[ month_index ]
                    
                    
                    current_datetime_ep = get_current_datetime_ep(2019, ep_current_month, ep_current_day, \
                                                                  ep_current_hour, ep_current_minute, local_time_zone )
                    

                    # Check BYPASS
                    if bypass_flag == True:
                        if real_time_flag == True:
                            utc_time = datetime.now(tz=pytz.UTC)
                            logger.info('########### RealTime CHECK ###########')
                            logger.info('{0}'.format(utc_time))
                            myrealtime = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(local_time_zone))
                            rt_hour = myrealtime.hour
                            rt_minute = myrealtime.minute
                            #logger.info('RealTime HOUR: {0}, RealTime MINUTE: {1}'.format(rt_hour, rt_minute))
                            #logger.info('Actual Time: {0}, Simulation Time: {1}'.format(rt_hour * 3600 + rt_minute * 60, ep.kStep * ep.deltaT))
                            print ("actual real time: ", myrealtime)

                            if current_datetime_ep >= sp.startDatetime:  
                            #if rt_hour * 3600 + rt_minute * 60 <= ep.kStep * ep.deltaT:                           
                                bypass_flag = False  # Stop bypass
                                logger.info('########### STOP BYPASS: Real Time ###########')
                            else:
                                logger.info('################# RealTime-and-BYPASS #################')
                                bypass_flag = True   # continue bypass
                                #pass
                        else:
                            #if sp.start_hour*3600+sp.start_minute*60 <= (ep.kStep-1)*ep.deltaT:
                            if current_datetime_ep >= sp.startDatetime:
                                bypass_flag = False     # Stop bypass
                                logger.info('########### STOP BYPASS: Hours ########')
                            else:
                                logger.info('################# non-realtime and BYPASS #################')
                                bypass_flag = True # continue bypass
                                #pass
                    else:
                        logger.info('############### SIMULATION --no bypass ###############')
                        #pass
                    
                    
                    if ep.flag != 0:
                        break
    
                    master_index = sp.variables.inputIndexFromVariableName("MasterEnable")
                    if bypass_flag:
                        ep.inputs[master_index] = 0
                    else:
                        ep.inputs = [0] * ((len(sp.variables.inputIds())) + 1)
                        ep.inputs[master_index] = 1
                        write_arrays = mongodb.writearrays
                        for array in write_arrays.find({"siteRef": sp.site_ref}):
                            logger.info("write array: %s" % array)
                            for val in array.get('val'):
                                if val:
                                    logger.info("val: %s" % val)
                                    index = sp.variables.inputIndex(array.get('_id'))
                                    if index == -1:
                                        logger.error('bad input index for: %s' % array.get('_id'))
                                    else:
                                        ep.inputs[index] = val
                                        ep.inputs[index + 1] = 1
                                        break
    
                    # Convert to tuple
                    inputs = tuple(ep.inputs)
    
                    # Print
                    logger.info('Time: {0}'.format((ep.kStep - 1) * ep.deltaT))
    
                    # Write to inputs of E+
                    ep.write(mlep.mlep_encode_real_data(2, 0, (ep.kStep - 1) * ep.deltaT, inputs))
        
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
                        # time computed for ouput purposes
                        '''
                        output_time = datetime.strptime(sp.start_date, "%m/%d").replace(year=startDatetime.year) \
                                             + timedelta(seconds=(ep.kStep-1)*ep.deltaT)
                        output_time = output_time.replace(tzinfo=pytz.utc)
                        output_time = output_time.replace(tzinfo=pytz.timezone(time_zone))
                        
                        output_time = (pytz.timezone(local_time_zone)).localize(output_time)
                        
                        
                        # Haystack uses ISO 8601 format like this "t:2015-06-08T15:47:41-04:00 New_York"
                        # the database can only recgonize the time-zone with: UTC, Denver, ....
                        # i will come back later with a function to parse the timezone 
                        
                        if 'Denver' in str(output_time.tzname()):
                               output_time_string = 't:%s %s' % (output_time.isoformat(), 'Denver') 
                        elif 'UTC' in str(output_time.tzname()):
                               output_time_string = 't:%s %s' % (output_time.isoformat(),output_time.tzname())
                        else:
                               output_time_string = 't:%s %s' % (output_time.isoformat(), 'Denver')
                        '''
                        
                        
                        output_time_string = 't:%s %s' % (current_datetime_ep.isoformat(), 'Denver')

     
                        recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.datetime": output_time_string, "rec.step": "n:" + str(real_time_step), "rec.simStatus": "s:Running"}}, False)
    
                    # Step
                    logger.info('Step: {0}/{1}'.format(ep.kStep, ep.MAX_STEPS))
    
                    # Advance time
                    ep.kStep = ep.kStep + 1

                    # Get current time
                    #utc_time = datetime.now(tz=pytz.UTC)
                    #next_t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(local_time_zone)) + \
                    #         timedelta(seconds=sp.rt_step_time)
                    next_t = t + sp.rt_step_time
                    #next_t = ep_current_time + timedelta(seconds=sp.rt_step_time)
                  
            except Exception as error:
                logger.error("Error while advancing simulation: %s", sys.exc_info()[0])
                traceback.print_exc()
                finalize_simulation()
                break
                # TODO: Cleanup simulation, and reset everything
         
        # Check Stop
        if ( ep.is_running == True and (ep.kStep > ep.MAX_STEPS) ) :
        #if ( ep.is_running == True and ( next_t >= end_time_unix) ) :
            stop = True; 
            
        elif ( sp.sim_status == 3 and ep.is_running == True ) :
            stop = True;
            
    
        if stop :
            try:
                #subprocess.call(['ReadVarsESO'])
                                                 
                finalize_simulation()
                ep.stop(True)      

                ep.is_running = 0
                sp.sim_status = 0
                # TODO: Need to wait for a signal of some sort that E+ is done, before removing stuff
                #finalize_simulation()
                logger.info('Simulation Terminated: Status: {0}, Step: {1}/{2}'.
                            format(sp.sim_status, ep.kStep, ep.MAX_STEPS))
                break
            except:
                logger.error("Error while attempting to stop / cleanup simulation")
                finalize_simulation()
                break
        
            # Done with simulation step
            # print('ping')
except:
    logger.error("Simulation error: %s", sys.exc_info()[0])
    traceback.print_exc()
    finalize_simulation()

