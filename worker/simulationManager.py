# !/usr/bin/env python

# -*- coding: utf-8 -*-

"""
 This script is for testing purposes only.

 (C) 2017 by Willy Bernal (Willy.BernalHeredia@nrel.gov)
"""
import mlep
import os
import boto3
import json
import time


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
            [processed, flag] = process_invoke_action_message(message_body)
        elif op == 'PointWrite':
            processed = process_write_point_message(message_body)
        if processed:
            message.delete()

    return


# Process Invoke Action Message
# Return true if the message was handled, otherwise false
def process_invoke_action_message(message_body):
    global sp
    action = message_body['action']

    # Start
    if action == 'start':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        time_step = 15  # Simulation time step
        sp.step_time = time_step*3600/message_body['time_scale']
        sp.start_date = message_body['start_date']
        sp.end_date = message_body['end_date']
        sp.start_hour = message_body['start_hour']
        sp.end_hour = message_body['end_hour']
        sp.accept_timeout = message_body['accept_timeout']*1000

        print('START')
        if not ep.is_running:
            flag = start_simulation()
            sp.start_time = time.time()
        else:
            flag = 0
        return True, flag
    # Pause
    elif action == 'pause':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        print('Pausing Simulation...')
        sp.sim_status = 2
        return True, 0
    elif action == 'resume':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        print('Resuming Simulation...')
        sp.sim_status = 1
        return True, 0
    # Stop
    elif action == 'stop':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        print('Stopping Simulation...')
        sp.sim_status = 3
        return True, 0
    # Unknown
    else:
        # Do nothing
        return False, 0


# Return true if the message was handled, otherwise false
def process_write_point_message(message_body):
    haystack_id = message_body['id']
    val = message_body['val']
    level = message_body['level']
    print("process_write_point_message: id = {haystack_id} val = {val} level = {level}".format(**locals()))
    # Master algorithm should assume that there is an extenal interface variable with name corresponding to haystack_id
    return True


def start_simulation():
    global sp
    global ep
    print('Starting EnergyPlus Simulation')

    # Arguments
    idf_file = '/Users/wbernalh/Documents/git/alfalfa/resources/CoSim/cosim.idf'
    weather_file = '/Applications/EnergyPlus-8-7-0/WeatherData/USA_MD_Baltimore-Washington.Intl.AP.724060_TMY3.epw'
    ep.accept_timeout = sp.accept_timeout
    mapping_file = "/Users/wbernalh/Documents/git/alfalfa/resources/CoSim/haystack_report_mapping.json"

    # Parse directory
    idf_file_details = os.path.split(idf_file)
    ep.workDir = idf_file_details[0]
    ep.arguments = (idf_file, weather_file)

    # Get Mapping
    [ep.inputs_list, ep.outputs_list] = mlep.mlep_parse_json(mapping_file)

    # Start EnergyPlus co-simulation
    (ep.status, ep.msg) = ep.start()

    # Check E+
    if ep.status != 0:
        raise Exception('Could not start EnergyPlus: %s.' % ep.msg)

    # Accept Socket
    [ep.status, ep.msg] = ep.accept_socket()

    if ep.status != 0:
        raise Exception('Could not connect EnergyPlus: %s.' % ep.msg)

    # The main simulation loop
    ep.deltaT = 15 * 60  # time step = 15 minutes
    ep.kStep = 1  # current simulation step
    ep.MAX_STEPS = 1 * 24 * 4 + 1  # max simulation time = 4 days
    ep.flag = 0

    # Simulation Status
    if ep.is_running:
        sp.sim_status = 1

    return ep.flag

# ======================================================= MAIN ========================================================
if __name__ == '__main__':
    # Initialized process
    ep = mlep.MlepProcess()
    sp = SimProcess()

    # Get the service resource
    sqs = boto3.resource('sqs')

    # Create the queue. This returns an SQS.Queue instance
    queue = sqs.create_queue(QueueName='test1', Attributes={'DelaySeconds': '0'})

    # Create a new message
    # response = queue.send_message(MessageBody='{"op":"InvokeAction",\
    # "action":"start", "time_step":6, "time_scale": 54000, "start_hour": "12:00",\
    # "start_date": "01/22", "end_hour": "12:00", "end_date": "01/26",\
    # "accept_timeout": 20}')
    # response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"pause_simulation"}')
    # response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"resume_simulation"}')
    # response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"stop_simulation"}')

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
            print(ep.kStep)

            if ep.flag != 0:
                break

            # Inputs
            inputs = (1, 1, 0)

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
        print('ping')
