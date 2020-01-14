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
from datetime import datetime


class AlfalfaConnections:
    """Create connections to data resources for Alfalfa"""

    def __init__(self):
        self.sqs = boto3.resource('sqs', region_name=os.environ['REGION'], endpoint_url=os.environ['JOB_QUEUE_URL'])
        self.queue = self.sqs.Queue(url=os.environ['JOB_QUEUE_URL'])
        self.s3 = boto3.resource('s3', region_name=os.environ['REGION'])

        self.mongo_client = MongoClient(os.environ['MONGO_URL'])
        self.mongodb = self.mongo_client[os.environ['MONGO_DB_NAME']]
        self.recs = self.mongodb.recs


class WorkerLogger:
    """A logger specific for the tasks of the Worker"""

    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
        self.logger = logging.getLogger('worker')
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.fh = logging.FileHandler('worker.log')
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)

        self.ch = logging.StreamHandler()
        self.ch.setFormatter(self.formatter)
        self.logger.addHandler(self.ch)


class Worker:
    """The Alfalfa worker class.  Used for processing messages from the boto3 SQS Queue resource"""

    def __init__(self):
        self.ac = AlfalfaConnections()
        self.worker_logger = WorkerLogger()

    def process_datetime_string(self, dt):
        """
        Check that datetime string has been correctly passed.
        Should be passed as: "%Y-%m-%d %H:%M:%S"

        :param str dt: datetime string
        :return: formatted time string
        """
        try:
            dt = datetime.strptime("%Y-%m-%d %H:%M:%S")
            return (dt.strftime("%Y-%m-%d %H:%M:%S"))
        except ValueError:
            self.worker_logger.logger.info("Invalid datetime string passed: {}".format(dt))
            sys.exit(1)

    def check_step_sim_config(self, message_body):
        """
        Check that the configuration parameters sent in the message for step_sim are valid.
        Message body must have exactly one of:
            - realtime.  expect 'true', 'false' or none provided
            - timescale.  expect int(), str that can be cast as an int, or none provided
            - external_clock. expect 'true', 'false', or none provided
        Optional parameters in message body:
            - startDatetime. Else, default is Jan 1st, 00:00:00 of current year.
                If realtime is specified, changed to current time.
            - endDatetime. Else, default is Dec 31st, 23:59:00 of current year

        start_datetime str : formatted as "%Y-%m-%d %H:%M:%S"
        end_datetime str : formatted as "%Y-%m-%d %H:%M:%S"
        step_sim_type str : one of 'realtime', 'timescale', 'external_clock'
        step_sim_val str : one of 'true' or 'int' where int is a castable integer

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :return: step_sim_type, step_sim_value, start_datetime, end_datetime
        """

        # TODO: Write test for this function
        year = datetime.today().year
        start = "{}-01-01 00:00:00".format(year)
        end = "{}-12-31 23:59:00".format(year)
        start_datetime = message_body.get('startDatetime',
                                          start)  # TODO change server side message: startDatetime to start_datetime
        end_datetime = message_body.get('endDatetime',
                                        end)  # TODO change server side message: endDatetime to end_datetime
        realtime = message_body.get('realtime', False) == 'true'
        timescale = message_body.get('timescale', False)  # type checking below in if statement
        external_clock = message_body.get('externalClock',
                                          False) == 'true'  # TODO change server side message: externalClock to external_clock

        # Only want one of: realtime, timescale, or external_clock.  Else, reject configuration.
        if (realtime and timescale) or (realtime and external_clock) or (timescale and external_clock):
            self.worker_logger.logger.info(
                "Only one of 'external_clock', 'timescale', or 'realtime' should be specified in message")
            sys.exit(1)

        # Check for at least one of the required parameters
        if not realtime and not timescale and not external_clock:
            # TODO: If exiting, what logging type to use?
            self.worker_logger.logger.info(
                "At least one of 'external_clock', 'timescale', or 'realtime' must be specified")
            sys.exit(1)

        if realtime:
            step_sim_type = "realtime"
            step_sim_value = "true"
            start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # TODO: epoch time?
        elif timescale:
            if str(timescale).isdigit():
                step_sim_type = "timescale"
                step_sim_value = str(timescale)
            else:
                self.worker_logger.logger.info("timescale: {} must be an integer value".format(timescale))
                sys.exit(1)
        elif external_clock:
            step_sim_type = "external_clock"
            step_sim_value = "true"

        # Check datetime string formatting
        start_datetime = self.process_datetime_string(start_datetime)
        end_datetime = self.process_datetime_string(end_datetime)

        return (step_sim_type, step_sim_value, start_datetime, end_datetime)

    def check_message_body(self, message_body, type):
        """
        Check that the message body contains minimum necessary keys before next step is processed.

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :param str type: One of 'add_site', 'step_sim', 'run_sim'
        :return:
        """
        if type == 'add_site':
            osm_name = message_body.get('osm_name', False)
            upload_id = message_body.get('upload_id', False)
            to_return = False if not osm_name or not upload_id else True
        elif type == 'step_sim':
            site_id = message_body.get('id', False)
            to_return = False if not site_id else True
        elif type == 'run_sim':
            upload_filename = message_body.get('upload_filename', False)
            upload_id = message_body.get('upload_id', False)
            to_return = False if not upload_filename or not upload_id else True
        return (to_return)

    def add_site(self, message_body):
        """
        Caller to add a site depending on the type of file to upload.
        Valid file extensions include: '.osm', '.zip', '.fmu'
        '.zip' file extensions expected for OpenStudio workflow directories.
        Site is added by spinning off a subprocess
        TODO: Document expected directory structure for OS workflows

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :return:
        """
        body_check = self.check_message_body(message_body, 'add_site')
        if not body_check:
            self.worker_logger.logger.info(
                'message_body for add_site does not have correct keys.  Site will not be added.')
            # TODO insert sys.exit(1)?
        else:
            osm_name = message_body.get('osm_name')
            upload_id = message_body.get('upload_id')
            self.worker_logger.logger.info('Add site for osm_name: %s, and upload_id: %s' % (osm_name, upload_id))

            # TODO reorganize the message names, because now "osm_name"
            #  is misleading because we are also handling FMUs
            name, ext = os.path.splitext(osm_name)
            if ext == '.osm':
                subprocess.call(['python', 'addosm/add_osm.py', osm_name, upload_id])
            elif ext == '.zip':
                # assume it contains an osw
                subprocess.call(['python3.5', 'addosw/add_osw.py', osm_name, upload_id])
            elif ext == '.fmu':
                subprocess.call(['python', 'addfmu/add_fmu.py', osm_name, upload_id])
            else:
                self.worker_logger.logger.info('Unsupported file type was uploaded')

    def step_sim(self, message_body):
        """
        Caller to step through a simulation.
        Valid simulation types include: '.osm', '.fmu'
        The simulation will not be started if an invalid simulation config is provided.
        Run occurs by spinning of a subprocess.

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :return:
        """
        body_check = self.check_message_body(message_body, 'step_sim')
        if not body_check:
            self.worker_logger.logger.info(
                'message_body for step_sim does not have correct keys.  Simulation will not be stepped through.')
            # TODO insert sys.exit(1)?
        else:
            site_id = message_body.get('id')
            site_rec = self.ac.recs.find_one({"_id": site_id})
            sim_type = site_rec.get("rec", {}).get("sim_type", "osm").replace("s:",
                                                                              "")  # TODO: do we still want default to be 'osm'?
            step_sim_type, step_sim_value, start_datetime, end_datetime = self.check_step_sim_config(message_body)
            self.worker_logger.logger.info('Start step_sim for site_id: %s, and sim_type: %s' % (site_id, sim_type))
            if sim_type == 'fmu':
                subprocess.call(
                    ['python', 'stepfmu/step_fmu.py', site_id, step_sim_type, step_sim_value, start_datetime,
                     end_datetime])
            elif sim_type == 'osm':
                subprocess.call(
                    ['python3.5', 'steposm/step_osm.py', site_id, step_sim_type, step_sim_value, start_datetime,
                     end_datetime])
            else:
                self.worker_logger.logger.info(
                    "Invalid simulation type: {}.  Only 'fmu' and 'osm' are currently supported".format(sim_type))
                sys.exit(1)

    def run_sim(self, message_body):
        """
        Run a simulation.  Running a simulation provides vanilla run of either an OSM or an FMU model.  Doesn't
        allow for external interfacing into model during runtime - simply runs the model.  Run occurs
        by spinning off a subprocess.

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :return:
        """
        body_check = self.check_message_body(message_body, 'run_sim')
        if not body_check:
            self.worker_logger.logger.info(
                'message_body for step_sim does not have correct keys.  Simulation will not be run.')
            # TODO insert sys.exit(1)?
        else:
            upload_filename = message_body.get('upload_filename')
            upload_id = message_body.get('upload_id')
            self.worker_logger.logger.info(
                'Run sim for upload_filename: %s, and upload_id: %s' % (upload_filename, upload_id))

            name, ext = os.path.splitext(upload_filename)
            if ext == '.gz':
                subprocess.call(['python3.5', 'simosm/sim_osm.py', upload_filename, upload_id])
            elif ext == '.fmu':
                subprocess.call(['python', 'simfmu/sim_fmu.py', upload_filename, upload_id])
            else:
                self.worker_logger.logger.info('Unsupported file type was uploaded')

    def process_message(self, message):
        """
        Process a single message from Queue.  Depending on operation requested, will call one of:
        - step_sim
        - add_site
        - run_sim

        :param message: A single message, as returned from a boto3 Queue resource
        :return:
        """
        try:
            message_body = json.loads(message.body)
            message.delete()
            op = message_body.get('op')
            if op == 'InvokeAction':
                action = message_body.get('action')
                # TODO change to step_sim
                if action == 'runSite':
                    self.step_sim(message_body)

                # TODO change to add_site
                elif action == 'addSite':
                    self.add_site(message_body)

                # TODO change to run_sim
                elif action == 'runSim':
                    self.run_sim(message_body)

        except Exception as e:
            print('Exception while processing message: %s' % e, file=sys.stderr)

    def run(self):
        """
        Listen to queue and process messages upon arrival

        :return:
        """
        while True:
            # WaitTimeSeconds triggers long polling that will wait for events to enter queue
            # Receive Message
            messages = self.ac.queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20)
            if len(messages) > 0:
                message = messages[0]
                self.worker_logger.info('Message Received with payload: %s' % message.body)
                # Process Message
                self.process_message(message)


if __name__ == '__main__':
    try:
        worker = Worker()
    except BaseException:  # TODO: what exceptions to catch?
        print('Exception while starting up worker', file=sys.stderr)
        sys.exit(1)

    try:
        worker.run()  # run the worker
    except BaseException:  # TODO: what exceptions to catch?
        pass
