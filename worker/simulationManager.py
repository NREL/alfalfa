# !/usr/bin/env python

# -*- coding: utf-8 -*-

"""
 This script is for testing purposes only.

 (C) 2017 by Willy Bernal (Willy.BernalHeredia@nrel.gov)
"""
from __future__ import print_function
import os
import boto3
import json
import shutil
import subprocess
import sys
import logging

# Process Message
def process_message(message):
    try:
        message_body = json.loads(message.body)
        message.delete()
        op = message_body.get('op')
        if op == 'InvokeAction':
            action = message_body.get('action')
            if action == 'start_simulation':
                site_ref = message_body.get('id','None')
                time_scale = message_body.get('time_scale','None')
                start_date = message_body.get('start_date','None')
                end_date = message_body.get('end_date','None')
                start_hour = message_body.get('start_hour','None')
                end_hour = message_body.get('end_hour','None')
                logger.info('Start simulation for site_ref: %s' % site_ref)
                subprocess.call(['python', 'runSimulation.py', site_ref, time_scale, start_date, end_date, start_hour, end_hour])
            elif action == 'add_site':
                osm_name = message_body.get('osm_name')
                upload_id = message_body.get('upload_id')
                logger.info('Add site for osm_name: %s, and upload_id: %s' % (osm_name, upload_id))
                subprocess.call(['python', 'addSite.py', osm_name, upload_id])
    except:
        print('Exception while processing message', file=sys.stderr)
# ======================================================= MAIN ========================================================
if __name__ == '__main__':
    try:
        sqs = boto3.resource('sqs', region_name='us-west-1', endpoint_url=os.environ['JOB_QUEUE_URL'])
        queue = sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
        s3 = boto3.resource('s3', region_name='us-west-1')

        logger = logging.getLogger('worker')
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        fh = logging.FileHandler('worker.log')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    except:
        print('Exception while starting up worker', file=sys.stderr)
        sys.exit(1)

    while True:
        # WaitTimeSeconds triggers long polling that will wait for events to enter queue
        # Receive Message
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=0)
        if len(messages) > 0:
            msg = messages[0]
            logger.info('Message Received with payload: %s' % msg.body)
            # Process Message
            process_message(msg)

