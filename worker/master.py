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
    elif op == 'PointWrite':
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
    haystack_id = message_body['id']
    val = message_body['val']
    level = message_body['level']
    print "process_write_point_message: id = {haystack_id} val = {val} level = {level}".format(**locals()) 
    # Master algorithm should assume that there is a extenal interface variable with name corresponding to haystack_id
    return True

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

