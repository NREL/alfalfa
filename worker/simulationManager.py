# !/usr/bin/env python

# -*- coding: utf-8 -*-

"""
 This script is for testing purposes only.

 This script is free software.

 (C) 2017 by Willy Bernal (Willy.BernalHeredia@nrel.gov)
"""
import mlep
import os
import boto3
import json
import time

def process_message(message):
    print('got a message')
    message_body = json.loads(message.body)
    processed = False

    op = message_body['op']
    # Message needs to be deleted, otherwise it will show back up in the queue for processing
    if op == 'InvokeAction':
        [processed, flag] = process_invoke_action_message(message_body)
    elif op == 'PointWrite':
        processed = process_write_point_message(message_body)
    if processed:
        message.delete()

    return


# Return true if the message was handled, otherwise false
def process_invoke_action_message(message_body):
    global ep
    global sim_status
    global start_time
    global step_time
    action = message_body['action']

    # Start
    if action == 'start':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        step_time = 5
        print('START')
        if not ep.isRunning:
            flag = start_simulation()
            start_time = time.time()
        else:
            flag = 0
        return True, flag
    # Pause
    elif action == 'pause':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        # (ep,status,deltaT,kStep,flag,MAXSTEPS) = start_simulation()
        print('PAUSE')
        sim_status = 2
        return True
    elif action == 'resume':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        # (ep,status,deltaT,kStep,flag,MAXSTEPS) = start_simulation()
        print('RESUME')
        sim_status = 1
        return True
    # Stop
    elif action == 'stop':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        # (ep,status,deltaT,kStep,flag,MAXSTEPS) = start_simulation()
        print('STOP')
        sim_status = 3
        return True
    # Unknown
    else:
        # Do nothing
        return False


# Return true if the message was handled, otherwise false
def process_write_point_message(message_body):
    haystack_id = message_body['id']
    val = message_body['val']
    level = message_body['level']
    print("process_write_point_message: id = {haystack_id} val = {val} level = {level}".format(**locals()))
    # Master algorithm should assume that there is an extenal interface variable with name corresponding to haystack_id
    return True


def start_simulation():
    global sim_status
    global ep
    print('Starting EnergyPlus Simulation')

    # Arguments
    idf_file = '/Users/wbernalh/Documents/git/alfalfa/resources/CoSim/cosim.idf'
    weather_file = '/Applications/EnergyPlus-8-7-0/WeatherData/USA_MD_Baltimore-Washington.Intl.AP.724060_TMY3.epw'
    ep.acceptTimeout = 20000
    mapping_file = "/Users/wbernalh/Documents/git/alfalfa/resources/CoSim/haystack_report_mapping.json"

    # Parse directory
    idf_file_details = os.path.split(idf_file)
    ep.workDir = idf_file_details[0]
    ep.arguments = (idf_file, weather_file)

    # Get Mapping
    [ep.inputs_list, ep.outputs_list] = mlep.mlepJSON(mapping_file)

    # Start EnergyPlus co-simulation
    (ep.status, ep.msg) = ep.start()

    # Check E+
    if ep.status != 0:
        raise Exception('Could not start EnergyPlus: %s.' % ep.msg)

    # Accept Socket
    [ep.status, ep.msg] = ep.acceptSocket()

    if ep.status != 0:
        raise Exception('Could not connect EnergyPlus: %s.' % ep.msg)

    # The main simulation loop
    ep.deltaT = 15 * 60  # time step = 15 minutes
    ep.kStep = 1  # current simulation step
    ep.MAXSTEPS = 1 * 24 * 4 + 1  # max simulation time = 4 days
    ep.flag = 0

    # Simulation Status
    if ep.isRunning:
        sim_status = 1

    return ep.flag


# Main loop
# 1. Process messages (start sim, set actuators, maybe other things)
# 2. Step simulation
# 3. Push current sensor values to database
# Create an mlepProcess instance 
ep = mlep.mlepProcess()
sim_status = 0
# 0 init
# 1 running
# 2 pause
# 3 stop

# Init
start_time = 0
step_time = 0
next_time = 0

# Get the service resource
sqs = boto3.resource('sqs')

# Create the queue. This returns an SQS.Queue instance
queue = sqs.create_queue(QueueName='test1', Attributes={'DelaySeconds': '0'})

# Get the queue. This returns an SQS.Queue instance
# queue = sqs.get_queue_by_name(QueueName='test1')

# Send two messages
# response = queue.send_messages(MessageBody='hello')
# Create a new message
# response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"start"}')
# response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"pause"}')
# response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"resume"}')
# response = queue.send_message(MessageBody='{"op":"InvokeAction","action":"stop"}')

# Receive Message
# message  = queue.receive_messages(MaxNumberOfMessages=1)
# print(message[0].message_id)
# print(message[0].body)
# print(message[0].message_attributes)
# print(type(message[0]))
# message[0].delete()

# Process messages by printing out body and optional author name
# for message in queue.receive_messages(
#    MessageAttributeNames=['Author'],
#    MaxNumberOfMessages=10):
#    # Get the custom author message attribute if it was set
#    author_text = ''
#    if message.message_attributes is not None:
#        author_name = message.message_attributes.get('Author').get('StringValue')
#        if author_name:
#            author_text = ' ({0})'.format(author_name)

# Print out the body and author (if set)
#    print('Hello, {0}!{1}'.format(message.body, author_text))

# Let the queue know that the message is processed
# message.delete()

while True:
    # WaitTimeSeconds triggers long polling that will wait for events to enter queue
    # Once this framework has the ability to run real simulations then the wait time
    # should probably be removed, because the simulation will establish a pace, perhaps
    # with some sleep commands to artificially slow things down to wall clock time
    messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=0)
    if len(messages) > 0:
        for msg in messages:
            print('Got Message')
            print(msg.body)

        process_message(messages[0])

    # Step simulation in time
    next_time = time.time()
    if ep.isRunning & (sim_status == 1) & (ep.kStep < ep.MAXSTEPS) & (next_time - start_time >= step_time):
        start_time = time.time()
        packet = ep.read()
        if packet == '':
            raise mlep.InputError('packet', 'Message Empty: %s.' % ep.msg)

        # Parse it to obtain building outputs
        [ep.flag, eptime, outputs] = mlep.mlepDecodePacket(packet)
        print(ep.kStep)

        if ep.flag != 0:
            break

        # Inputs
        inputs = (1, 1, 0)

        # Write to inputs of E+
        ep.write(mlep.mlepEncodeRealData(2, 0, (ep.kStep - 1) * ep.deltaT, inputs))

        # Advance time
        ep.kStep = ep.kStep + 1

        # Push latest point values to database
        # Need to do

    # Check Stop
    if ep.isRunning & (ep.kStep >= ep.MAXSTEPS):
        ep.stop(True)
        ep.isRunning = 0
        sim_status = 0

    # Done with simulation step    
    print('ping')
