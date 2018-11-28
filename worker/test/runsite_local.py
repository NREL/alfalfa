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
#from parsevariables import Variables
import sys
#sys.path.append('/home/mindcoder/alfalfa/worker/runsite/parsevariables')
from parsevariables import Variables
import mlep
import subprocess
import logging
import re
from datetime import date, datetime, timedelta
import pytz
import calendar
import traceback
from dateutil.parser import parse
import tarfile

# Time Zone
def utc_to_local(utc_dt):
    # get integer timestamp to avoid precision lost
    timestamp = calendar.timegm(utc_dt.timetuple())
    local_dt = datetime.fromtimestamp(timestamp)
    assert utc_dt.resolution >= timedelta(microseconds=1)
    return local_dt.replace(microsecond=utc_dt.microsecond)


# Replace Date
def replace_idf_settings(idf_file, pattern, date_start, date_end, time_step):
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

    
    # Overwrite File
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
               elif i == line_runperiod + 5:
                  line = end_month_line
               elif i == line_runperiod + 6:
                  line = end_day_line         
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
        self.sim_step_per_hour = 60     # Simulation steps per hour
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
    #tar_name = "%s.tar.gz" % sp.site_ref
    pass
    #tar_file = tarfile.open(tar_name, "w:gz")
    #tar_file.add(sp.workflow_directory, filter=reset, arcname=site_ref)
    #tar_file.close()
    
    #subprocess.call(['ReadVarsESO'])
    
    #bucket.upload_file(tar_name, "simulated/%s" % tar_name)
    
    #os.remove(tar_name)
    #shutil.rmtree(sp.workflow_directory)

    #recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}, "$unset": {"rec.datetime": ""} }, False)
    #recs.update_many({"_id": sp.site_ref, "rec.cur": "m:"}, {"$unset": {"rec.curVal": "", "rec.curErr": ""}, "$set": { "rec.curStatus": "s:disabled" } }, False)


def check_localtime(user_start_datetime, user_end_datetime, time_zone):
    '''This function will check if the time-inputs-from-user are local or not;
    This function will use UTC time as a reference. \
    The idea is: different time zones will have differences in the hour value generally, \
    and sometimes day value for corner cases'''
    
    #obtain the UTC time first
    datetime_utcnow = datetime.utcnow()
    print("****** Yanfei: datetime--utcnow: ", str(datetime_utcnow) )
    
    #check the UTC time zone
    print("****** Yanfei: time zone: ", time.tzname) 
    
    #obtain the hour and minute from UTC time
    utcnow_hour   = int(str(datetime_utcnow)[11:13])
    utcnow_minute = int(str(datetime_utcnow)[14:16])
    print("****** Yanfei: utcnow hour: ", utcnow_hour)
    print("****** Yanfei: utcnow minute: ", utcnow_minute)

    #obtain the hour and minute from user-inputs
    start_datetime_str=str(user_start_datetime)
    end_datetime_str=str(user_end_datetime)
     
    print("****** Yanfei: start datetime: ", start_datetime_str)
    print("****** Yanfei: end datetime: ", end_datetime_str)
    start_datetime_hour_user   = int(start_datetime_str[11:13])
    start_datetime_minute_user = int(start_datetime_str[14:16])
    print("****** Yanfei: start hour: ", start_datetime_hour_user)

    #obtain the local timeie from user; here use Denver as a demo    
    local_timezone = pytz.timezone('America/Denver')    
    local_datetime = pytz.UTC.localize(datetime.utcnow()).astimezone(local_timezone)
    local_hour     = local_datetime.strftime('%H') 

    if (start_datetime_hour_user == utcnow_hour) or (start_datetime_hour_user != local_hour):
        start_datetime = local_datetime
        end_datetime   = user_end_datetime.astimezone(local_timezone)
        print("starting/eding local time: ",(start_datetime, end_datetime))
    else:  
        start_datetime = user_start_datetime
        end_datetime   = user_end_datetime
        print("starting local time: ", (start_datetime, end_datetime))
    
    return (start_datetime, end_datetime)

###############################################################################
###############    Main Entry for runsite_local.py    #########################
###############################################################################
'''
bashcommand="""head -1 /proc/self/cgroup|cut -d/ -f3"""
x=subprocess.check_output(['bash','-c',bashcommand])
print("*** Hey Yanfei ***: ", x)
'''

yy=os.listdir("/test/parse_local/")

#bashcommand2="""docker-compose ps -q"""
#x2=subprocess.check_output(['bash','-c', bashcommand2])
print("****** Hey Yanfei-2: ****** ", yy)

#osm_path="/home/mindcoder/alfalfa/worker/test/parse_local/52e40666-a939-49ce-b403-ea08247b379d/workflow/run/"
osm_path="/test/"
print(os.listdir(osm_path))

y5=subprocess.check_output(['find','/','-name','openstudio'])
print(y5)
 
y4=subprocess.call(['openstudio', osm_path+'translate_osm.rb', osm_path+'in.osm', 'yanfei_test.idf'])
print("**** Yanfei-3: *** ", y4)      
print("*** Yanfei Good!*** ")

mytimezone = 'America/Denver'

local_timezone = pytz.timezone(mytimezone)
start_datetime_local = pytz.UTC.localize(datetime.utcnow()).astimezone(local_timezone)

print(" *** starting datetime: worker-test ***: ", start_datetime_local)

str_start_datetime=start_datetime_local.strftime('%Y-%m-%d %H:%M:%S-%f')
print(str_start_datetime)

end_datetime_local = start_datetime_local + timedelta(hours=1)
print(" *** ending datetime: worker-test ***: ", end_datetime_local)

site_ref = 'yanfei_test'
real_time_flag = False
time_scale = 60  


(startDatetime, endDatetime) = check_localtime(start_datetime_local, end_datetime_local, mytimezone)

#print (startDatetime, endDatetime)

start_date = "%02d/%02d" % (startDatetime.month, startDatetime.day)
start_hour = startDatetime.hour
start_minute = startDatetime.minute
end_date = "%02d/%02d" % (endDatetime.month, endDatetime.day)
end_hour = endDatetime.hour
end_minute = endDatetime.minute

sim_path = 'test/simulate'
folder_local_test = os.path.join(sim_path, site_ref)
if not os.path.exists(folder_local_test):
    os.makedirs(folder_local_test)
    print("folder-local-test is not existed; however it is created now!")

folder_tmp="/test/parse_local/52e40666-a939-49ce-b403-ea08247b379d/"

#copy idf file to the running folder:
idf_old_path = os.path.join('/test/','yanfei_test.idf')
idf_new_path = os.path.join(folder_tmp, "workflow/run/yanfei_test.idf")
print(idf_new_path)

shutil.copyfile(idf_old_path, idf_new_path)


sp = SimProcess()
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
sp.idf = os.path.join(folder_tmp, "workflow/run/%s" % sp.site_ref)
sp.weather = os.path.join(folder_tmp, 'workflow/files/weather.epw')
sp.mapping = os.path.join(folder_tmp, 'workflow/reports/haystack_report_mapping.json')
sp.workflow_directory = folder_local_test

#the variables.cfg file need to reside in the same folder of idf
cfg_variables_old_path = os.path.join(folder_tmp, 'workflow/reports/export_bcvtb_report_variables.cfg')
cfg_variables_new_path = os.path.join(folder_tmp, 'workflow/run/variables.cfg')
shutil.copyfile(cfg_variables_old_path, cfg_variables_new_path)
sp.variables = Variables(cfg_variables_new_path, sp.mapping)

sp.sim_step_time = 60 / sp.sim_step_per_hour * 60  # Simulation time step - seconds
bypass_flag = True
sim_date = replace_idf_settings( '/test/yanfei_test.idf', 'RunPeriod,', sp.start_date, sp.end_date, sp.sim_step_per_hour)
print("****** Yanfei:Actual Date: ******: ", sim_date)
sp.rt_step_time = sp.sim_step_time / float(time_scale)


ep = mlep.MlepProcess()
ep.bcvtbDir = '/root/bcvtb/'
ep.env = {'BCVTB_HOME': '/root/bcvtb'}
ep.accept_timeout = sp.accept_timeout
ep.mapping = sp.mapping
ep.flag = 0

ep.workDir = os.path.join(folder_tmp, 'workflow/run/')
ep.arguments = (sp.idf+'.idf', sp.weather)
print("****** EP Arguments ******", ep.arguments)

# Start EnergyPlus co-simulation
(ep.status, ep.msg) = ep.start()

# Check E+
if ep.status != 0:
    print('Could not start EnergyPlus: %s.' % ep.msg)
    ep.flag = 1
else:
    print('****** EnergyPlus Started ******')

print("*** ep.program *** ", ep.program)
print("*** ep.env ***: ", ep.env)

# Accept Socket
[ep.status, ep.msg] = ep.accept_socket()
print("****** Socket Status/Msg: ****** ", (ep.status, ep.msg) )

if ep.status != 0:
    print('Could not connect EnergyPlus: %s.' % ep.msg)
    ep.flag = 1

# The main simulation loop
ep.deltaT = sp.sim_step_time    # time step - sec
ep.kStep = 1                    # current simulation step
# Days
d0 = date(2017, sim_date[0], sim_date[1])
d1 = date(2017, sim_date[2], sim_date[3])
delta = d1 - d0
ep.MAX_STEPS = (24 * delta.days + sp.end_hour) * sp.sim_step_per_hour + sp.end_minute + 1# Max. Number of Steps

# Simulation Status
if ep.is_running == True:
    sp.sim_status = 1
    
# Set next step
utc_time = datetime.now(tz=pytz.UTC)
t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(mytimezone))
next_t = t



try:

    # Simulation Status
    if ep.is_running == True:
        sp.sim_status = 1
    
    # Set next step
    utc_time = datetime.now(tz=pytz.UTC)
    t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(mytimezone))
    next_t = t
    
    #recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Starting"}}, False)
    
    # probably need some kind of fail safe/timeout to ensure
    # that this is not an infinite loop
    # or maybe a timeout in the python call to this script
    while True:
        stop = False;
    
        sp.next_time = time.time()
        utc_time = datetime.now(tz=pytz.UTC)
        t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(mytimezone))
    
        # Iterating over timesteps
        #    if (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and (sp.next_time - sp.start_time >= sp.rt_step_time)) or\
        if (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and t >= next_t) or\
                (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and bypass_flag):  # Bypass Time
            #logger.info('E+ Running: {0}, Sim Status: {1}, E+ Step: {2}, Elapsed step time: {3}, RT Step Time: {4}'.format(
            #    ep.is_running, sp.sim_status, ep.kStep, sp.next_time - sp.start_time, sp.rt_step_time))
            #logger.info('###### t: {0}'.format(t))
            try:
                # Check for "Stopping" here so we don't hit the database as fast as the event loop will run
                # Instead we only check the database for stopping at each simulation step
                #rec = recs.find_one({"_id": sp.site_ref})
                #if rec and (rec.get("rec",{}).get("simStatus") == "s:Stopping") :
                #    print("Stopping")
                #    stop = True;
    
                if stop == False:
                    # Check BYPASS
                    if bypass_flag == True:
                        if real_time_flag == True:
                            utc_time = datetime.now(tz=pytz.UTC)
                            print('########### RT CHECK ###########')
                            print('{0}'.format(utc_time))
                            rt_hour = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(time_zone)).hour
                            rt_minute = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(time_zone)).minute
                            print('RT HOUR: {0}, RT MINUTE: {1}'.format(rt_hour, rt_minute))
                            #logger.info('Actual Time: {0}, Simulation Time: {1}'.format(rt_hour * 3600 + rt_minute * 60, ep.kStep * ep.deltaT))
                            if rt_hour * 3600 + rt_minute * 60 <= ep.kStep * ep.deltaT:
                                bypass_flag = False  # Stop bypass
                                #logger.info('########### STOP BYPASS: RT ###########')
                            else:
                                #logger.info('################# RT-BYPASS #################')
                                pass
                        else:
                            if sp.start_hour*3600+sp.start_minute*60 <= (ep.kStep-1)*ep.deltaT:
                                bypass_flag = False     # Stop bypass
                                #logger.info('########### STOP BYPASS: Hours ########')
                            else:
                                #logger.info('################# BYPASS #################')
                                pass
                    else:
                        #logger.info('############### SIMULATION ###############')
                        pass
                    
    
                    # Read packet
                    # Get current time
                    utc_time = datetime.now(tz=pytz.UTC)
                    next_t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(mytimezone)) + \
                             timedelta(seconds=sp.rt_step_time)
                    packet = ep.read()
                    # logger.info('Packet: {0}'.format(packet))
                    if packet == '':
                        raise mlep.InputError('packet', 'Message Empty: %s.' % ep.msg)
        
                    # Parse it to obtain building outputs
                    [ep.flag, eptime, outputs] = mlep.mlep_decode_packet(packet)
                    # Log Output Data
                    ep.outputs = outputs
                    #print("***Yanfei Checking Outputs coming from EnergyPlus*** ", outputs)
                    passed_current_day=outputs[-4]
                    passed_current_hour=outputs[-3]
                    passed_current_minute=outputs[-2]
                    passed_current_month=outputs[-1]
                    if ep.kStep==ep.MAX_STEPS:
                        print("***\n Yanfei Checking Outputs coming from EnergyPlus*** ", passed_current_day, passed_current_hour, passed_current_minute, passed_current_month)
        
                    if ep.flag != 0:
                        break
                   
                    #print("****** Yanfei input IDs******: ", sp.variables.inputIds())
                    #print("****** Yanfei input ID length ***", len(sp.variables.inputIds()))
                    #time.sleep(100) 
                    '''
                    master_index = sp.variables.inputIndexFromVariableName("MasterEnable")
                    if bypass_flag:
                        ep.inputs[master_index] = 0 #disable the coupling of MLEP
                    else:
                        print("****** Yanfei input IDs******: ", sp.variables.inputIds())
                        sys.sleep(100)
                        ep.inputs = [0] * ((len(sp.variables.inputIds())) + 1)
                        ep.inputs[master_index] = 1 #enable the coupling of MLEP
                        write_arrays = mongodb.writearrays
                        for array in write_arrays.find({"siteRef": sp.site_ref}):
                            #logger.info("write array: %s" % array)
                            for val in array.get('val'):
                                if val:
                                    #logger.info("val: %s" % val)
                                    index = sp.variables.inputIndex(array.get('_id'))
                                    if index == -1:
                                        print('bad input index for: %s' % array.get('_id'))
                                    else:
                                        ep.inputs[index] = val
                                        ep.inputs[index + 1] = 1
                                        break
                    '''
                    ep.inputs = [1] * (21)
                    # Convert to tuple
                    inputs = tuple(ep.inputs)
    
                    # Print
                    print('Time: {0}'.format((ep.kStep - 1) * ep.deltaT))
    
                    # Write to inputs of E+
                    ep.write(mlep.mlep_encode_real_data(2, 0, (ep.kStep - 1) * ep.deltaT, inputs))
        
                    if bypass_flag == False:
                        for output_id in sp.variables.outputIds():
                            output_index = sp.variables.outputIndex(output_id)
                            if output_index == -1:
                                print('bad output index for: %s' % output_id)
                            else:
                                output_value = ep.outputs[output_index]
                                # print("*** Yanfei: Checking output_id: ",output_id)
                                # TODO: Make this better with a bulk update
                                # Also at some point consider removing curVal and related fields after sim ends
                                #recs.update_one({"_id": output_id}, {
                                #    "$set": {"rec.curVal": "n:%s" % output_value, "rec.curStatus": "s:ok", "rec.cur": "m:"}}, False)
    
                        # time computed for ouput purposes
                        output_time = datetime.strptime(sp.start_date, "%m/%d").replace(year=startDatetime.year) + timedelta(seconds=(ep.kStep-1)*ep.deltaT)
                        #output_time = output_time.replace(tzinfo=pytz.utc)
                        #output_time = output_time.replace(tzinfo=pytz.timezone(time_zone))
                        #print("\n********** Yanfei: outputtime to browser initial: ", output_time)
                        output_time = (pytz.timezone(mytimezone)).localize(output_time)
                        print("\n********** Yanfei: outputtime to browser: ", output_time)
                        # Haystack uses ISO 8601 format like this "t:2015-06-08T15:47:41-04:00 New_York"
                        # the database can only recgonize the time-zone with: UTC, Denver, ....
                        # i will come back later with a function to parse the timezone 
                        if 'Denver' in str(output_time.tzname()):
                               output_time_string = 't:%s %s' % (output_time.isoformat(), 'Denver') 
                        elif 'UTC' in str(output_time.tzname()):
                               output_time_string = 't:%s %s' % (output_time.isoformat(),output_time.tzname())
                        else:
                               output_time_string = 't:%s %s' % (output_time.isoformat(), 'Denver')
                        
                        #output_time_string = 't:%s %s' % (output_time.isoformat(),output_time.tzname())
                       
                        #recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.datetime": output_time_string, "rec.simStatus": "s:Running"}}, False)
    
                    # Step
                    print('Step: {0}/{1}'.format(ep.kStep, ep.MAX_STEPS))
    
                    # Advance time
                    ep.kStep = ep.kStep + 1
                    #print("\n***Yanfei kstep check-1: ", ep.kStep)
                    #if ep.kStep==ep.MAX_STEPS+1:
                    #    subprocess.call(['ReadVarsESO']) 
            except Exception as error:
                print("Error while advancing simulation: %s", sys.exc_info()[0])
                traceback.print_exc()
                finalize_simulation()
                break
                # TODO: Cleanup simulation, and reset everything
        
        # Check Stop
        if ( ep.is_running == True and (ep.kStep > ep.MAX_STEPS) ) :
            stop = True; 
            print("*** Yanfei: i am in category-1")
        elif ( sp.sim_status == 3 and ep.is_running == True ) :
            stop = True;
            print("*** Yanfei:: i am in category-2")
    
        if stop :
            try:
                #subprocess.call(['ReadVarsESO'])
                print("\n *** Yanfei kstep check-2: ", ep.kStep)
                                 
                finalize_simulation()
                ep.stop(True)
                #packet = ep.read()
                #[ep.flag, eptime, outputs] = mlep.mlep_decode_packet(packet)
                #print("*** Yanfei: ep-flag: ", ep.flag)
                #print("***Yanfei: eptime: ", eptime)
                #print("***Yanfei: outputs: ", outputs)       

                ep.is_running = 0
                sp.sim_status = 0
                # TODO: Need to wait for a signal of some sort that E+ is done, before removing stuff
                #finalize_simulation()
                #logger.info('Simulation Terminated: Status: {0}, Step: {1}/{2}'.
                #            format(sp.sim_status, ep.kStep, ep.MAX_STEPS))
                break
            except:
                #logger.error("Error while attempting to stop / cleanup simulation")
                finalize_simulation()
                break
        
            # Done with simulation step
            # print('ping')
except:
    print("Simulation error: %s", sys.exc_info()[0])
    traceback.print_exc()
    finalize_simulation()
time.sleep(1000)

