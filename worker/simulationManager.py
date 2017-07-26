# !/usr/bin/env python

# -*- coding: utf-8 -*-

"""
 This script is for testing purposes only.

 (C) 2017 by Willy Bernal (Willy.BernalHeredia@nrel.gov)
"""
import mlep
import os
import ast
import boto3
import json
import time
import tarfile
import shutil
from subprocess import call


# Simulation Process Class
class SimProcess:
    def __init__(self):
        self.sim_status = 0             # 0=init, 1=running, 2=pause, 3=stop
        self.step_time = 0              # Real-time step
        self.start_time = 0             # Real-time step
        self.next_time = 0              # Real-time step
        self.start_date = '01/01'       # Start date for simulation (01/01)
        self.end_date = '12/31'         # End date for simulation (12/31)
        self.start_hour = 1             # Start hour for simulation (1-23)
        self.end_hour = 23              # End hour for simulation (1-23)
        self.accept_timeout = 10000     # Accept timeout for simulation (ms)
        self.idf = None                 # EnergyPlus file path (/path/to/energyplus/file)
        self.weather = None             # Weather file path (/path/to/weather/file)


# Process Message
def process_message(message):
    print('got a message')
    try:
        processed = False
        message_body = json.loads(message.body)
    except Exception as e:
        print('Exception: {0}'.format(e))
        message.delete()
    else:
        op = message_body['op']
        # Message needs to be deleted, otherwise it will show back up in the queue for processing
        if op == 'InvokeAction':
            processed = process_invoke_action_message(message_body)
        elif op == 'PointWrite':
            processed = process_write_point_message(message_body)

        if processed:
            print('Message processed successfully:\n{}'.format(message_body))
        else:
            print('Message could not be processed:\n{}'.format(message_body))

        # Delete Message
        message.delete()

    return


# Process Invoke Action Message
# Return true if the message was handled, otherwise false
def process_invoke_action_message(message_body):
    global sp
    global ep
    action = message_body['action']

    # Start
    if action == 'start_simulation':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        time_step = 15  # Simulation time step
        sp.step_time = time_step*3600/message_body['time_scale']
        sp.start_date = message_body['start_date']
        sp.end_date = message_body['end_date']
        sp.start_hour = message_body['start_hour']
        sp.end_hour = message_body['end_hour']
        sp.accept_timeout = message_body['accept_timeout']*1000
        sp.idf = message_body['arguments']['idf']
        sp.weather = message_body['arguments']['weather']
        sp.mapping = message_body['mapping']

        print('Starting Simulation')
        if not ep.is_running:
            start_simulation()
            sp.start_time = time.time()
        return True
    # Pause
    elif action == 'pause_simulation':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        print('Pausing Simulation...')
        sp.sim_status = 2
        return True
    elif action == 'resume_simulation':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        print('Resuming Simulation...')
        sp.sim_status = 1
        return True
    # Stop
    elif action == 'stop_simulation':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        print('Stopping Simulation...')
        sp.sim_status = 3
        return True
    # Add Site
    elif action == 'add_site':
        print('Adding New Site...')
        add_new_site(message_body['site_name'])
        return True
    # Unknown
    else:
        # Do nothing
        return False

# Download an osm file and use OpenStudio Haystack measure to 
# add a new haystack site
def add_new_site(site_name):
    print(site_name)
    if not local_flag:
        key = "uploads/%s" % (site_name)
        basename = os.path.splitext(site_name)[0]
        directory = os.path.join('/work',basename)
        seedpath = os.path.join(directory,'seed.osm')
        workflowpath = os.path.join(directory,'workflow/workflow.osw')
        jsonpath = os.path.join(directory,'workflow/reports/haystack_report_haystack.json');

        if not os.path.exists(directory):
            os.makedirs(directory)

        tar = tarfile.open("workflow.tar.gz")
        tar.extractall(directory)
        tar.close()

        time.sleep(5)

        bucket = s3.Bucket('alfalfa')
        bucket.download_file(key, seedpath)

        call(['openstudio', 'run', '-m', '-w', workflowpath])

        call(['npm', 'run', 'start', jsonpath])

        def reset(tarinfo):
            tarinfo.uid = tarinfo.gid = 0
            tarinfo.uname = tarinfo.gname = "root"
            return tarinfo

        tarname = "%s.tar.gz" % (basename)
        tar = tarfile.open(tarname, "w:gz")
        tar.add(directory, filter=reset)
        tar.close()

        bucket.upload_file(tarname, "parsed/%s" % (tarname) )

        os.remove(tarname)
        shutil.rmtree(directory)

    return

# Return true if the message was handled, otherwise false
def process_write_point_message(message_body):
    global ep

    try:
        haystack_id = message_body['haystack_id']
        val = message_body['val']
        print("process_write_point_message: id = {haystack_id}, val = {val}".format(**locals()))
        # Get index
        index = ep.inputs_list.index(haystack_id)
        # Update Inputs list
        ep.inputs[index] = 1
        ep.inputs[index+1] = val
    except:
        flag = False
    else:
        flag = True
    return flag


# Start Simulation
def start_simulation():
    global sp
    global ep
    print('Starting EnergyPlus Simulation')

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
    ep.inputs = [0] * (len(ep.inputs_list)+1)

    # Start EnergyPlus co-simulation
    (ep.status, ep.msg) = ep.start()

    # Check E+
    if ep.status != 0:
        print('Could not start EnergyPlus: %s.' % ep.msg)
        ep.flag = 1

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

    return

# ======================================================= MAIN ========================================================
if __name__ == '__main__':
    # Initialized process
    ep = mlep.MlepProcess()
    sp = SimProcess()
    if 'JOB_QUEUE_URL' in os.environ:
        local_flag = False
    else:
        local_flag = True

    # ============= SQS Queue =============
    if local_flag:
        # Get the service resource
        sqs = boto3.resource('sqs')
        # Create the queue. This returns an SQS.Queue instance
        queue = sqs.create_queue(QueueName='test1', Attributes={'DelaySeconds': '0'})
    else:
        # Define a remote queue
        sqs = boto3.resource('sqs', region_name='us-west-1', endpoint_url=os.environ['JOB_QUEUE_URL'])
        queue = sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
        s3 = boto3.resource('s3', region_name='us-west-1')

    # ============= Messages Available =============
    # response = queue.send_message(MessageBody='{"op":"InvokeAction",\
    # "action":"start_simulation", \
    # "arguments":{"idf": "/Users/wbernalh/Documents/git/alfalfa/resources/CoSim/cosim.idf",\
    # "weather": "USA_MD_Baltimore-Washington.Intl.AP.724060_TMY3.epw"},\
    # "mapping":"/Users/wbernalh/Documents/git/alfalfa/resources/CoSim/haystack_report_mapping.json",\
    # "time_step":6, "time_scale": 54000, "start_hour": "12:00",\
    # "start_date": "01/22", "end_hour": "12:00", "end_date": "01/26",\
    # "accept_timeout": 20}')
    # response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"pause_simulation"}')
    # response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"resume_simulation"}')
    # response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"stop_simulation"}')
    # response = queue.send_message(MessageBody='{"op":"PointWrite",\
    # "haystack_id":"VAV_mid_WITH_REHEAT_Outside_Air_Damper_CMD","val":1}')

    while True:
        # WaitTimeSeconds triggers long polling that will wait for events to enter queue
        # Receive Message
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=0)
        if len(messages) > 0:
            for msg in messages:
                print('Got Message')
                print(msg.body)
            # Process Message
            process_message(messages[0])

        # Step simulation in time
        # Adjust next real-time simulation step
        sp.next_time = time.time()
        if ep.is_running and (sp.sim_status == 1) and (ep.kStep < ep.MAX_STEPS) and \
                (sp.next_time - sp.start_time >= sp.step_time):
            sp.start_time = time.time()
            packet = ep.read()
            if packet == '':
                raise mlep.InputError('packet', 'Message Empty: %s.' % ep.msg)

            # Parse it to obtain building outputs
            [ep.flag, eptime, outputs] = mlep.mlep_decode_packet(packet)
            # Log Output Data
            ep.outputs = outputs
            print(ep.kStep)

            if ep.flag != 0:
                break

            # Inputs
            inputs = tuple(ep.inputs)

            # Write to inputs of E+
            ep.write(mlep.mlep_encode_real_data(2, 0, (ep.kStep - 1) * ep.deltaT, inputs))

            # Advance time
            ep.kStep = ep.kStep + 1

            # Push latest point values to database
            # Need to do

        # Check Stop
        if (ep.is_running and (ep.kStep >= ep.MAX_STEPS)) or (sp.sim_status == 3 and ep.is_running):
            ep.stop(True)
            ep.is_running = 0
            sp.sim_status = 0
            print('Simulation Terminated')

        # Done with simulation step
        #print('ping')
