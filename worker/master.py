import time
import boto3
import os
import json

sqs = boto3.resource('sqs', region_name='us-west-2', endpoint_url=os.environ['JOB_QUEUE_URL'])
queue = sqs.Queue(url=os.environ['JOB_QUEUE_URL'])

def process_message(message):
    print 'got a message'
    message_body = json.loads(message.body)
    processed = False;

    op = message_body['op']
    # Message needs to be deleted, otherwise it will show back up in the queue for processing
    if op == 'InvokeAction': 
        processed = process_invoke_action_message(message_body)
    elif op == 'WritePoint':
        processed = process_write_point_message(message_body)

    if processed:
        message.delete()
        
    return

# Return true if the message was handled, otherwise false
def process_invoke_action_message(message_body):
    action = message_body['action']

    if action == 'Start':
        # Enhancement: Make this take arguments to a particular model (idf/osm)
        # Consider some global information to keep track of any simulation that is running
        start_simulation()
        return True
    # some other type of InvokeAction
    #elif ...
    return False

# Return true if the message was handled, otherwise false
def process_write_point_message(message_body):
    tags = message_body['tags']
    print tags
    # or whatever the tags are for an economizer point
    if ['equip','ahu','economizer'] <= tags:
        process_economizer_write_point(message_body)
        return True
    # elif ['x','y','z'] ...
        # process_xyz_write

    return False

# This needs to map a point write to actual actuators in the simulation
# Coordinate with Haystack measure
# Here is one for an economizer point write
def process_economizer_write_point(message_body):
    # Use message_body for additional context and information
    # May need to insert additional "meta" tag information in the message
    # depending on the type of point written to

    # This assumes there is a simulation running
    # probably need some global information about the simulation, if any, that is running
    print 'Writing economizer point'
    return

# There can be a wide range of process_foo_write_point methods
# for all of the types of points that may be written
#def process_xyz_write_point:
#    return

def start_simulation():
    print 'Starting EnergyPlus Simulation'
    return

# Main loop 
# 1. Process messages (start sim, set actuators, maybe other things)
# 2. Step simulation
# 3. Push current sensor values to database
# Easy as 1,2,3 ! :)
while True:
    # WaitTimeSeconds triggers long polling that will wait for events to enter queue
    # Once this framework has the ability to run real simulations then the wait time
    # should probably be removed, because the simulation will establish a pace, perhaps
    # with some sleep commands to artificially slow things down to wall clock time
    messages = queue.receive_messages(MaxNumberOfMessages = 1, WaitTimeSeconds = 5)
    if len(messages) > 0:
        process_message(messages[0])

    # Step simulation in time

    # Push latest point values to database

    print 'ping'

