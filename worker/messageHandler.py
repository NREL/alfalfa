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

# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import boto3
import json
import subprocess
import sys
import logging
from pymongo import MongoClient

# Process Message
def process_message(message):
    try:
        message_body = json.loads(message.body)
        message.delete()
        op = message_body.get('op')
        if op == 'InvokeAction':
            action = message_body.get('action')
            if action == 'runSite':
                siteRef = message_body.get('id', 'None')
                startDatetime = message_body.get('startDatetime', 'None')
                endDatetime = message_body.get('endDatetime', 'None')
                realtime = message_body.get('realtime', 'None')
                timescale = str(message_body.get('timescale', 'None'))

                site = recs.find_one({"_id": siteRef})
                simType = site.get("rec",{}).get("simType", "osm").replace("s:","")

                logger.info('Start simulation for site_ref: %s, and simType: %s' % (siteRef, simType))

                if simType == 'fmu':
                    subprocess.call(['python', 'runfmusite/runFMUSite.py', siteRef, realtime, timescale, startDatetime, endDatetime])
                else:
                    subprocess.call(['python3.5', 'runsite/runSite.py', siteRef, realtime, timescale, startDatetime, endDatetime])
            elif action == 'addSite':
                osm_name = message_body.get('osm_name')
                upload_id = message_body.get('upload_id')
                logger.info('Add site for osm_name: %s, and upload_id: %s' % (osm_name, upload_id))

                # TODO reorganize the message names, because now "osm_name"
                # is misleading because we are also handling FMUs
                name, ext = os.path.splitext(osm_name)
                if ext == '.osm':
                    #subprocess.call(['python3.5', 'addsite/addSite.py', osm_name, upload_id])
                    subprocess.call(['python', 'addsite/addSite.py', osm_name, upload_id])
                elif ext == '.fmu':
                    subprocess.call(['python', 'addfmusite/addFMUSite.py', osm_name, upload_id])
                else:
                    logger.info('Unsupported file type was uploaded')
            elif action == 'runSim':
                upload_filename = message_body.get('upload_filename')
                upload_id = message_body.get('upload_id')
                logger.info('Run sim for upload_filename: %s, and upload_id: %s' % (upload_filename, upload_id))

                name, ext = os.path.splitext(upload_filename)
                if ext == '.gz':
                    subprocess.call(['python3.5', 'runsimulation/runSimulation.py', upload_filename, upload_id])
                elif ext == '.fmu':
                    subprocess.call(['python', 'runfmusimulation/runFMUSimulation.py', upload_filename, upload_id])
                else:
                    logger.info('Unsupported file type was uploaded')

    except Exception as e:
        print('Exception while processing message: %s' % e, file=sys.stderr)

# ======================================================= MAIN ========================================================
if __name__ == '__main__':
    try:
        sqs = boto3.resource('sqs', region_name='us-east-1', endpoint_url=os.environ['JOB_QUEUE_URL'])
        queue = sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
        s3 = boto3.resource('s3', region_name='us-east-1')

        mongo_client = MongoClient(os.environ['MONGO_URL'])
        mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
        recs = mongodb.recs

        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
        logger = logging.getLogger('worker')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        fh = logging.FileHandler('worker.log')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    except:
        print('Exception while starting up worker', file=sys.stderr)
        sys.exit(1)

    while True:
        # WaitTimeSeconds triggers long polling that will wait for events to enter queue
        # Receive Message
        messages = queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20)
        if len(messages) > 0:
            msg = messages[0]
            logger.info('Message Received with payload: %s' % msg.body)
            # Process Message
            process_message(msg)
        else:
            if "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI" in os.environ:
                ecsclient = boto3.client('ecs', region_name='us-east-1')
                response = ecsclient.describe_services(cluster='worker_ecs_cluster',services=['worker-service'])['services'][0]
                desiredCount = response['desiredCount']
                runningCount = response['runningCount']
                pendingCount = response['pendingCount']
                minimumCount = 1

                if ((runningCount > minimumCount) & (desiredCount > minimumCount)):
                    ecsclient.update_service(cluster='worker_ecs_cluster',
                        service='worker-service',
                        desiredCount=(desiredCount - 1))
                    sys.exit(0)

