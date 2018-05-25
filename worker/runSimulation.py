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
from datetime import date, datetime, timedelta
import pytz
import calendar
import traceback
from dateutil.parser import parse

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

    # Generate Lines
    begin_month_line = '  {},                                      !- Begin Month\n'.format(begin_month)
    begin_day_line = '  {},                                      !- Begin Day of Month\n'.format(begin_day)
    end_month_line = '  {},                                      !- End Month\n'.format(end_month)
    end_day_line = '  {},                                      !- End Day of Month\n'.format(end_day)
    time_step_line = '  {};                                      !- Number of Timesteps per Hour\n'.format(time_step)

    # Overwrite File
    count = 0
    count_ts = 0
    with open(idf_file, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        for line in lines:
            if pattern in line:
                count = 5
            elif count > 4:
                # Do nothing
                count = count - 1
            elif count == 4:
                # Begin Month
                line = begin_month_line
                count = count - 1
            elif count == 3:
                # Begin Day
                line = begin_day_line
                count = count - 1
            elif count == 2:
                # End Month
                line = end_month_line
                count = count - 1
            elif count == 1:
                # End day
                line = end_day_line
                count = count - 1
            elif 'Timestep,' in line:
                # Time step
                count_ts = 1
            elif count_ts == 1:
                # Replace
                line = time_step_line
                count_ts = 0
            # Write Every line
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
    # tar_name = "%s.tar.gz" % sp.site_ref
    tar_file = tarfile.open(tar_name, "w:gz")
    tar_file.add(sp.workflow_directory, filter=reset, arcname=site_ref)
    tar_file.close()

    bucket.upload_file(tar_name, "simulated/%s" % tar_name)
    os.remove(tar_name)
    shutil.rmtree(sp.workflow_directory)

    recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Stopped"}}, False)
    recs.update_one({"_id": sp.site_ref}, {"$unset": {"rec.datetime": ""}}, False)


startDatetime = datetime.today()

# TODO: Kyle to pass this arguments. Uncomment once included.
if len(sys.argv) == 6:

    print('runSimulation called with arguments: %s.' % sys.argv, file=sys.stderr)
    site_ref = sys.argv[1]
    real_time_flag = sys.argv[2]
    time_scale = sys.argv[3]

    startDatetime = parse(sys.argv[4])
    endDatetime = parse(sys.argv[5])

    start_date = "%02d/%02d" % (startDatetime.month,startDatetime.day)
    start_hour = startDatetime.hour
    start_minute = startDatetime.minute

    end_date = "%02d/%02d" % (endDatetime.month,endDatetime.day)
    end_hour = endDatetime.hour
    end_minute = endDatetime.minute    

    # time_zone = sys.argv[8]
    time_zone = 'America/Denver'
    # sim_step_per_hour = sys.argv[9]
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

logger = logging.getLogger('simulation')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log_file = os.path.join(directory, 'simulation.log')
fh = logging.FileHandler(log_file)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)


sqs = boto3.resource('sqs', region_name='us-east-1', endpoint_url=os.environ['JOB_QUEUE_URL'])
queue = sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
s3 = boto3.resource('s3', region_name='us-east-1')
# Mongo Database
mongo_client = MongoClient(os.environ['MONGO_URL'])
mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
recs = mongodb.recs

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

bucket = s3.Bucket('alfalfa')
bucket.download_file(key, tarpath)

tar = tarfile.open(tarpath)
tar.extractall(sim_path)
tar.close()

sp.variables = Variables(variables_path, sp.mapping)

subprocess.call(['openstudio', 'translate_osm.rb', osmpath, sp.idf])
shutil.copyfile(variables_path, variables_new_path)

if sp.real_time_flag == True:
    # Set Time Scale
    sp.time_scale = 1
else:
    if sp.time_scale > 120:
        sp.time_scale = 120

# Simulation Parameters
sp.sim_step_time = 60 / sp.sim_step_per_hour * 60  # Simulation time step - seconds
bypass_flag = True
sim_date = replace_idf_settings(sp.idf + '.idf', 'RunPeriod,', sp.start_date, sp.end_date, sp.sim_step_per_hour)
try:
    sp.rt_step_time = sp.sim_step_time / float(time_scale)    # Seconds
except:
    sp.rt_step_time = 10                                    # Seconds

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
d0 = date(2017, sim_date[0], sim_date[1])
d1 = date(2017, sim_date[2], sim_date[3])
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
t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(time_zone))
next_t = t

recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Starting"}}, False)

# probably need some kind of fail safe/timeout to ensure
# that this is not an infinite loop
# or maybe a timeout in the python call to this script
while True:
    stop = False;

    sp.next_time = time.time()
    utc_time = datetime.now(tz=pytz.UTC)
    t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(time_zone))

    # Iterating over timesteps
    #    if (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and (sp.next_time - sp.start_time >= sp.rt_step_time)) or\
    if (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and t >= next_t) or\
            (ep.is_running and (sp.sim_status == 1) and (ep.kStep <= ep.MAX_STEPS) and bypass_flag):  # Bypass Time
        logger.info('E+ Running: {0}, Sim Status: {1}, E+ Step: {2}, Elapsed step time: {3}, RT Step Time: {4}'.format(
            ep.is_running, sp.sim_status, ep.kStep, sp.next_time - sp.start_time, sp.rt_step_time))
        logger.info('###### t: {0}'.format(t))
        try:
            # Check for "Stopping" here so we don't hit the database as fast as the event loop will run
            # Instead we only check the database for stopping at each simulation step
            rec = recs.find_one({"_id": sp.site_ref})
            if rec and (rec.get("rec",{}).get("simStatus") == "s:Stopping") :
                logger.info("Stopping")
                stop = True;

            if stop == False:
                # Check BYPASS
                if bypass_flag == True:
                    if real_time_flag == True:
                        utc_time = datetime.now(tz=pytz.UTC)
                        logger.info('########### RT CHECK ###########')
                        logger.info('{0}'.format(utc_time))
                        rt_hour = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(time_zone)).hour
                        rt_minute = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(time_zone)).minute
                        logger.info('RT HOUR: {0}, RT MINUTE: {1}'.format(rt_hour, rt_minute))
                        logger.info('Actual Time: {0}, Simulation Time: {1}'.format(rt_hour * 3600 + rt_minute * 60, ep.kStep * ep.deltaT))
                        if rt_hour * 3600 + rt_minute * 60 <= ep.kStep * ep.deltaT:
                            bypass_flag = False  # Stop bypass
                            logger.info('########### STOP BYPASS: RT ###########')
                        else:
                            logger.info('################# RT-BYPASS #################')
                    else:
                        if sp.start_hour*3600+sp.start_minute*60 <= (ep.kStep-1)*ep.deltaT:
                            bypass_flag = False     # Stop bypass
                            logger.info('########### STOP BYPASS: Hours ########')
                        else:
                            logger.info('################# BYPASS #################')
                else:
                    logger.info('############### SIMULATION ###############')
                

                # Read packet
                # Get current time
                utc_time = datetime.now(tz=pytz.UTC)
                next_t = utc_time.astimezone(pytz.utc).astimezone(pytz.timezone(time_zone)) + \
                         timedelta(seconds=sp.rt_step_time)
                packet = ep.read()
                # logger.info('Packet: {0}'.format(packet))
                if packet == '':
                    raise mlep.InputError('packet', 'Message Empty: %s.' % ep.msg)
    
                # Parse it to obtain building outputs
                [ep.flag, eptime, outputs] = mlep.mlep_decode_packet(packet)
                # Log Output Data
                ep.outputs = outputs
    
                if ep.flag != 0:
                    break

                master_index = sp.variables.inputIndexFromVariableName("MasterEnable")
                if bypass_flag:
                    ep.inputs[master_index] = 0
                else:
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

                    # time computed for ouput purposes
                    output_time = datetime.strptime(sp.start_date, "%m/%d").replace(year=startDatetime.year) + timedelta(seconds=(ep.kStep-1)*ep.deltaT)
                    output_time = output_time.replace(tzinfo=pytz.utc)
                    # Haystack uses ISO 8601 format like this "t:2015-06-08T15:47:41-04:00 New_York"
                    output_time_string = 't:%s %s' % (output_time.isoformat(),output_time.tzname())
                    recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.datetime": output_time_string, "rec.simStatus": "s:Running"}}, False)

                # Step
                logger.info('Step: {0}/{1}'.format(ep.kStep, ep.MAX_STEPS))

                # Advance time
                ep.kStep = ep.kStep + 1

        except Exception as error:
            logger.error("Error while advancing simulation: %s", sys.exc_info()[0])
            traceback.print_exc()
            finalize_simulation()
            break
            # TODO: Cleanup simulation, and reset everything
    
    # Check Stop
    if ( ep.is_running == True and (ep.kStep > ep.MAX_STEPS) ) :
        stop = True;
    elif ( sp.sim_status == 3 and ep.is_running == True ) :
        stop = True;
    if stop :
        try:
            ep.stop(True)
            ep.is_running = 0
            sp.sim_status = 0

            # TODO: Need to wait for a signal of some sort that E+ is done, before removing stuff
            finalize_simulation()
            logger.info('Simulation Terminated: Status: {0}, Step: {1}/{2}'.
                        format(sp.sim_status, ep.kStep, ep.MAX_STEPS))
            break
        except:
            logger.error("Error while attempting to stop / cleanup simulation")
            finalize_simulation()
            break
    
        # Done with simulation step
        # print('ping')
