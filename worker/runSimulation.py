import sys
import os
import boto3
import json
import tarfile
import shutil
import time
#from shutil import copyfile
from pymongo import MongoClient
import pprint
from parsevariables import Variables
import sys

if len(sys.argv) == 7:
    site_ref = sys.argv[1]
    time_scale = sys.argv[2]
    start_date = sys.argv[3]
    end_date = sys.argv[4]
    start_hour = sys.argv[5]
    end_hour = sys.argv[6]
else:
    print('runSimulation called with incorrect number of arguments: %s.' % len(sys.argv))
    sys.exit()

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

if not local_flag and sp.site_ref:
    sim_path = '/simulate'
    directory = os.path.join(sim_path, sp.site_ref)
    tarname = "%s.tar.gz" % sp.site_ref
    key = "parsed/%s" % tarname
    tarpath = os.path.join(directory, tarname)
    osmpath = os.path.join(directory, 'workflow/run/in.osm')
    sp.idf = os.path.join(directory, "workflow/run/%s" % sp.site_ref)
    sp.weather = os.path.join(directory, 'workflow/files/weather.epw')
    sp.mapping = os.path.join(directory, 'workflow/reports/haystack_report_mapping.json')
    sp.workflow_directory = directory
    variables_path = os.path.join(directory, 'workflow/reports/export_bcvtb_report_variables.cfg')
    variables_new_path = os.path.join(directory, 'workflow/run/variables.cfg')

    if not os.path.exists(directory):
        os.makedirs(directory)

    bucket = s3.Bucket('alfalfa')
    bucket.download_file(key, tarpath)

    tar = tarfile.open(tarpath)
    tar.extractall(sim_path)
    tar.close()

    sp.variables = Variables(variables_path,sp.mapping)

    call(['openstudio', 'translate_osm.rb', osmpath, sp.idf])
    shutil.copyfile(variables_path, variables_new_path)

# Arguments
ep.accept_timeout = sp.accept_timeout
ep.mapping = sp.mapping
ep.flag = 0

# Parse directory
idf_file_details = os.path.split(sp.idf)
ep.workDir = idf_file_details[0]
ep.arguments = (sp.idf, sp.weather)

# Get Mapping
[ep.outputs_list, ep.inputs_list] = mlep.mlep_parse_json(ep.mapping)
# Initialize input tuplet
ep.inputs = [0] * ((len(sp.variables.inputIds())) + 1)

# Start EnergyPlus co-simulation
(ep.status, ep.msg) = ep.start()

# Check E+
if ep.status != 0:
    print('Could not start EnergyPlus: %s.' % ep.msg)
    ep.flag = 1
else:
    print('EnergyPlus Started')

# Accept Socket
[ep.status, ep.msg] = ep.accept_socket()

if ep.status != 0:
    print('Could not connect EnergyPlus: %s.' % ep.msg)
    ep.flag = 1

# The main simulation loop
ep.deltaT = 15 * 60  # time step = 15 minutes
ep.kStep = 1  # current simulation step
ep.MAX_STEPS = 1 * 24 * 4 + 1  # max simulation time = 4 days

# Simulation Status
if ep.is_running:
    sp.sim_status = 1

