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

import time
import boto3
import os
import json

sqs = boto3.resource('sqs', region_name='us-east-1', endpoint_url=os.environ['JOB_QUEUE_URL'])
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

