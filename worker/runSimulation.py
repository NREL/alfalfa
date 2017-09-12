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

if len(sys.argv) == 7:
    site_ref = sys.argv[1]
    time_scale = sys.argv[2]
    start_date = sys.argv[3]
    end_date = sys.argv[4]
    start_hour = sys.argv[5]
    end_hour = sys.argv[6]
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


# Replace Date
def replace_date(idf_file, pattern, start_date, end_date):
    # Parse Date
    begin_month = [int(s) for s in re.findall(r'\d+', start_date)][0]
    begin_day = [int(s) for s in re.findall(r'\d+', start_date)][1]
    end_month = [int(s) for s in re.findall(r'\d+', end_date)][0]
    end_day = [int(s) for s in re.findall(r'\d+', end_date)][1]

    # Generate Lines
    begin_month_line = '  {},                                      !- Begin Month\n'.format(begin_month)
    begin_day_line = '  {},                                      !- Begin Day of Month\n'.format(begin_day)
    end_month_line = '  {},                                      !- End Month\n'.format(end_month)
    end_day_line = '  {},                                      !- End Day of Month\n'.format(end_day)

    # Overwrite File
    count = 0
    with open(idf_file, 'r+') as f:
        lines = f.readlines()
        f.seek(0)
        f.truncate()
        for line in lines:
            if pattern in line:
                count = 6
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
            # Write Every line
            f.write(line)


# Simulation Process Class
class SimProcess:
    def __init__(self):
        self.sim_status = 0  # 0=init, 1=running, 2=pause, 3=stop
        self.step_time = 20  # Real-time step
        self.start_time = 0  # Real-time step
        self.next_time = 0  # Real-time step
        self.start_date = '01/01'  # Start date for simulation (01/01)
        self.end_date = '12/31'  # End date for simulation (12/31)
        self.start_hour = 1  # Start hour for simulation (1-23)
        self.end_hour = 23  # End hour for simulation (1-23)
        self.accept_timeout = 10000  # Accept timeout for simulation (ms)
        self.idf = None  # EnergyPlus file path (/path/to/energyplus/file)
        self.mapping = None
        self.weather = None  # Weather file path (/path/to/weather/file)
        self.site_ref = None
        self.workflow_directory = None
        self.variables = None


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

#    tar = tarfile.open(tar_name, "w:gz")
#    tar.add(directory, filter=reset, arcname=site_ref)
#    tar.close()
#
#    bucket.upload_file(tar_name, "parsed/%s" % tar_name)
#    os.remove(tar_name)

sqs = boto3.resource('sqs', region_name='us-west-1', endpoint_url=os.environ['JOB_QUEUE_URL'])
queue = sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
logger.info('JOB_QUEUE_URL: %s' % os.environ['JOB_QUEUE_URL'])
s3 = boto3.resource('s3', region_name='us-west-1')
# Mongo Database
mongo_client = MongoClient(os.environ['MONGO_URL'])
logger.info('MONGO_URL: %s' % os.environ['MONGO_URL'])
logger.info('########################################################################')
logger.info(os.environ['MONGO_DB_NAME'])
mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
recs = mongodb.recs

time_step = 15  # Simulation time step
sp = SimProcess()
ep = mlep.MlepProcess()

ep.bcvtbDir = '/root/bcvtb/'
ep.env = {'BCVTB_HOME': '/root/bcvtb'}

try:
    sp.step_time = time_step * 3600 / int(time_scale)
except:
    sp.step_time = 20
    
if start_date != 'None':
    sp.start_date = start_date
if end_date != 'None':
    sp.end_date = end_date
if start_hour != 'None':
    sp.start_hour = start_hour
if end_hour != 'None':
    sp.end_hour = end_hour
if 'site_ref' != 'None':
    sp.site_ref = site_ref

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

# Set date
sp.start_date = '01/01'
sp.end_date = '01/05'
replace_date(sp.idf, 'RunPeriod,', sp.start_date, sp.end_date)

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
ep.deltaT = 15 * 60  # time step conversion min -> sec
ep.kStep = 1  # current simulation step
ep.MAX_STEPS = 1 * 24 * 4 + 1  # max simulation time = 4 days

# Simulation Status
if ep.is_running:
    sp.sim_status = 1

sp.start_time = time.time()

recs.update_one({"_id": sp.site_ref}, {"$set": {"rec.simStatus": "s:Running"}}, False)

# probably need some kind of fail safe/timeout to ensure
# that this is not an infinite loop
# or maybe a timeout in the python call to this script
while True:
    sp.next_time = time.time()
    if ep.is_running and (sp.sim_status == 1) and (ep.kStep < ep.MAX_STEPS) and (
            sp.next_time - sp.start_time >= sp.step_time):
        try:
            logger.info('step: %s' % ep.kStep)
            sp.start_time = time.time()
            packet = ep.read()
            if packet == '':
                raise mlep.InputError('packet', 'Message Empty: %s.' % ep.msg)
    
            # Parse it to obtain building outputs
            [ep.flag, eptime, outputs] = mlep.mlep_decode_packet(packet)
            # Log Output Data
            ep.outputs = outputs
    
            if ep.flag != 0:
                break
    
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
    
            # Write to inputs of E+
            ep.write(mlep.mlep_encode_real_data(2, 0, (ep.kStep - 1) * ep.deltaT, inputs))
    
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
    
            # Advance time
            ep.kStep = ep.kStep + 1
        except:
            logger.error("Error while advancing simulation: %s", sys.exc_info()[0])
            finalize_simulation()
            break
            # TODO: Cleanup simulation, and reset everything
    
    # Check Stop
    if (ep.is_running and (ep.kStep >= ep.MAX_STEPS)) or (sp.sim_status == 3 and ep.is_running):
        try:
            ep.stop(True)
            ep.is_running = 0
            sp.sim_status = 0
            # TODO: Need to wait for a signal of some sort that E+ is done, before removing stuff
            time.sleep(5)
            finalize_simulation()
            logger.info('Simulation Terminated')
            break
        except:
            logger.error("Error while attempting to stop / cleanup simulation")
            finalize_simulation()
            break
    
        # Done with simulation step
        # print('ping')
