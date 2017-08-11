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
from shutil import copyfile
from pymongo import MongoClient


# Simulation Process Class
class SimProcess:
    def __init__(self):
        self.sim_status = 0             # 0=init, 1=running, 2=pause, 3=stop
        self.step_time = 20              # Real-time step
        self.start_time = 0             # Real-time step
        self.next_time = 0              # Real-time step
        self.start_date = '01/01'       # Start date for simulation (01/01)
        self.end_date = '12/31'         # End date for simulation (12/31)
        self.start_hour = 1             # Start hour for simulation (1-23)
        self.end_hour = 23              # End hour for simulation (1-23)
        self.accept_timeout = 10000     # Accept timeout for simulation (ms)
        self.idf = None                 # EnergyPlus file path (/path/to/energyplus/file)
        self.mapping = None
        self.weather = None             # Weather file path (/path/to/weather/file)
        self.site_ref = None
        self.workflow_directory = None


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
            # Only delete if we successfully handled it
            # Otherwise wait for worker to try again
            message.delete()
        else:
            print('Message could not be processed:\n{}'.format(message_body))

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
        sp = SimProcess()
        if 'time_scale' in message_body:
            sp.step_time = time_step*3600/int(message_body['time_scale'])
        if 'start_date' in message_body:
            sp.start_date = message_body['start_date']
        if 'end_date' in message_body:
            sp.end_date = message_body['end_date']
        if 'start_hour' in message_body:
            sp.start_hour = message_body['start_hour']
        if 'end_hour' in message_body:
            sp.end_hour = message_body['end_hour']
        if 'accept_timeout' in message_body:
            sp.accept_timeout = message_body['accept_timeout']*1000
        if 'idf' in message_body:
            sp.idf = message_body['idf']
        if 'weather' in message_body:
            sp.weather = message_body['weather']
        if 'mapping' in message_body:
            sp.mapping = message_body['mapping']
        if 'id' in message_body:
            sp.site_ref = message_body['id']

        print(sp.site_ref)

        if not ep.is_running:
            print('Starting Simulation')
            start_simulation()
            sp.start_time = time.time()
            return True

        return False
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
        if not ep.is_running:
            print('Adding New Site...')
            add_new_site(message_body['osm_name'], message_body['upload_id'])
            return True

        return False
    # Unknown
    else:
        # Do nothing
        return False

# Download an osm file and use OpenStudio Haystack measure to 
# add a new haystack site
def add_new_site(osm_name, upload_id):
    print(osm_name)
    if not local_flag:
        key = "uploads/%s/%s" % (upload_id, osm_name)
        basename = os.path.splitext(osm_name)[0]
        directory = os.path.join('/parse',upload_id)
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

        site_ref = False
        with open(jsonpath) as json_file:    
            data = json.load(json_file)
            for entity in data:
                if 'site' in entity:
                    if entity['site'] == 'm:':
                        site_ref = entity['id'].replace('r:','')
                        break;

        if site_ref:

            # This adds a new haystack site to the database
            call(['npm', 'run', 'start', jsonpath, site_ref])

            # Open the json file and get a site reference
            # Store the results by site ref
            def reset(tarinfo):
                tarinfo.uid = tarinfo.gid = 0
                tarinfo.uname = tarinfo.gname = "root"
                return tarinfo

            tarname = "%s.tar.gz" % (site_ref)
            tar = tarfile.open(tarname, "w:gz")
            tar.add(directory, filter=reset, arcname=site_ref)
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

    try:
        if not local_flag and sp.site_ref:
            sim_path = '/simulate'
            directory = os.path.join(sim_path,sp.site_ref)
            tarname = "%s.tar.gz" % (sp.site_ref)
            key = "parsed/%s" % (tarname)
            tarpath = os.path.join(directory,tarname)
            osmpath = os.path.join(directory,'workflow/run/in.osm')
            sp.idf = os.path.join(directory,"workflow/run/%s" % sp.site_ref)
            sp.weather = os.path.join(directory,'workflow/files/weather.epw')
            sp.mapping = os.path.join(directory,'workflow/reports/haystack_report_mapping.json')
            sp.workflow_directory = directory
            variables_path = os.path.join(directory,'workflow/reports/export_bcvtb_report_variables.cfg')
            variables_new_path = os.path.join(directory,'workflow/run/variables.cfg')

            if not os.path.exists(directory):
                os.makedirs(directory)

            bucket = s3.Bucket('alfalfa')
            bucket.download_file(key, tarpath)

            tar = tarfile.open(tarpath)
            tar.extractall(sim_path)
            tar.close()

            call(['openstudio', 'translate_osm.rb', osmpath, sp.idf])
            copyfile(variables_path,variables_new_path)

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
    except Exception as e:
        print('MLEP failed to start due to an Exception: {0}'.format(e))
        return

# ======================================================= MAIN ========================================================
if __name__ == '__main__':
    # Initialized process
    ep = mlep.MlepProcess()
    ep.bcvtbDir = '/root/bcvtb/'
    ep.env = {'BCVTB_HOME': '/root/bcvtb'}
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
        mongo_client = MongoClient(os.environ['MONGO_URL'])
        mongodb = mongo_client.admin

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

            #for item in ep.inputs_list:
            #    write_array = mongo.getWriteArray(item)
            #    value = write_array.getCurrentWinningValue
            #    ep.inputs[ep.inputs.index(id)] = value
            if not local_flag:
                write_arrays = mongodb.writearrays
                for array in write_arrays.find({"siteRef": sp.site_ref}):
                    for val in array.get('val'):
                       if val: 
                            ep.inputs[ep.inputs_list.index(array.get('_id'))] = val
                            break;

                inputs = tuple(ep.inputs)

                # Write to inputs of E+
                ep.write(mlep.mlep_encode_real_data(2, 0, (ep.kStep - 1) * ep.deltaT, inputs))
                
                # Push latest point values to database
                #values_to_insert = []
                recs = mongodb.recs
                for output in ep.outputs_list:
                    output_index = ep.outputs_list.index(output)
                    output_value = ep.outputs[output_index]
                    output_doc = {"_id": output, "curVal": output_value}
                    # TODO: Make this better with a bulk update
                    # Also at some point consider removing curVal and related fields after sim ends
                    recs.update_one({"_id": output},{"$set": { "rec.curVal": "n:%s" % output_value, "rec.curStatus": "s:ok", "rec.cur": "m:" } },False)
                    #values_to_insert.append(output_doc)
                
                #cur_values.update_many({'_id': {'$in': values_to_insert}}, {'$set': {'$in': values_to_insert}})

            # Advance time
            ep.kStep = ep.kStep + 1

        # Check Stop
        if (ep.is_running and (ep.kStep >= ep.MAX_STEPS)) or (sp.sim_status == 3 and ep.is_running):
            ep.stop(True)
            ep.is_running = 0
            sp.sim_status = 0
            # TODO: Need to wait for a signal of some sort that E+ is done, before removing stuff
            time.sleep(5)
            shutil.rmtree(sp.workflow_directory)
            print('Simulation Terminated')

        # Done with simulation step
        #print('ping')
