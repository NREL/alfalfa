########################################################################################################################
#  Copyright (c) 2008-2022, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
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
import subprocess
import sys
from datetime import datetime

from alfalfa_worker.worker_job_base import WorkerJobBase
from alfalfa_worker.lib.utils import process_datetime_string


class WorkerOpenStudio(WorkerJobBase):
    """The Alfalfa alfalfa_worker class.  Used for processing messages
    from the boto3 SQS Queue resource"""

    def __init__(self):
        super().__init__()

    def check_step_sim_config(self, message_body, sim_type):
        """
        Check that the configuration parameters sent in the message for step_sim are valid.
        Message body must have exactly one of:
            - realtime.  expect 'true', 'false' or none provided
            - timescale.  expect int(), str that can be cast as an int, or none provided
            - external_clock. expect 'true', 'false', or none provided
        Optional parameters in message body:
            if sim_type == fmu
                - startDatetime. Else, default is 0.
                - endDatetime. Else, default is number of seconds in year
            else
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

        if sim_type == 'osm':
            year = datetime.today().year
            start = "{}-01-01 00:00:00".format(year)
            end = "{}-12-31 23:59:00".format(year)
        else:
            start = "0"
            end = str(60 * 60 * 24 * 365)

        # TODO change server side message: startDatetime to start_datetime
        start_datetime = message_body.get('startDatetime', start)
        if start_datetime == 'undefined':
            start_datetime = start
        # TODO change server side message: endDatetime to end_datetime
        end_datetime = message_body.get('endDatetime', end)
        if end_datetime == 'undefined':
            end_datetime = end

        realtime = message_body.get('realtime', False) == 'true'
        timescale = message_body.get('timescale', False)  # type checking below in if statement
        timescale = False if timescale == 'undefined' else timescale
        # TODO change server side message: externalClock to external_clock
        external_clock = message_body.get('externalClock', False) == 'true'

        # TODO remove after tests written
        self.worker_logger.logger.info(
            "start_datetime type: {}\tstart_datetime: {}".format(type(start_datetime), start_datetime))
        self.worker_logger.logger.info(
            "end_datetime type: {}\tend_datetime: {}".format(type(end_datetime), end_datetime))
        self.worker_logger.logger.info("realtime type: {}\trealtime: {}".format(type(realtime), realtime))
        self.worker_logger.logger.info("timescale type: {}\ttimescale: {}".format(type(timescale), timescale))
        self.worker_logger.logger.info(
            "external_clock type: {}\texternal_clock: {}".format(type(external_clock), external_clock))
        # Only want one of: realtime, timescale, or external_clock.  Else, reject configuration.
        # if (realtime and timescale) or (realtime and external_clock) or (timescale and external_clock):
        #    self.worker_logger.logger.info(
        #        "Only one of 'external_clock', 'timescale', or 'realtime' should be specified in message")
        #    sys.exit(1)

        # Check for at least one of the required parameters
        if not realtime and not timescale and not external_clock:
            # TODO: If exiting, what logging type to use?
            self.worker_logger.logger.info(
                "At least one of 'external_clock', 'timescale', or 'realtime' must be specified")
            sys.exit(1)

        if external_clock:
            step_sim_type = "external_clock"
            step_sim_value = "true"
        elif realtime:
            step_sim_type = "realtime"
            step_sim_value = 1
        elif timescale:
            if str(timescale).isdigit():
                step_sim_type = "timescale"
                step_sim_value = int(timescale)
            else:
                self.worker_logger.logger.info(f"timescale: {timescale} must be an integer value")
                sys.exit(1)

        # Check datetime string formatting
        if sim_type == 'osm':
            start_datetime = process_datetime_string(start_datetime, logger=self.worker_logger.logger)
            end_datetime = process_datetime_string(end_datetime, logger=self.worker_logger.logger)

        return (step_sim_type, step_sim_value, start_datetime, end_datetime)

    def add_site_type(self, p, file_name, upload_id):
        """
        Simple wrapper for the add_site subprocess call given the path for python file to call

        :param p: path of add_site/add_site.py file to call
        :param file_name: name of file to add with extension, excludes full path
        :param upload_id:
        :return:
        """
        if not os.path.isfile(p):
            self.worker_logger.logger.info("No file: {}".format(p))
        else:
            return_code = subprocess.call(['python3', p, file_name, upload_id])
            self.check_subprocess_call(return_code, file_name, 'add_site')

    def step_sim_type(self, site_id, step_sim_type, step_sim_value, start_datetime, end_datetime, model_type):
        """Simple wrapper for the step_sim subprocess call given required params

        :param p:
        :param site_id:
        :param step_sim_type:
        :param step_sim_value:
        :param start_datetime:
        :param end_datetime:
        :param model_type: string, type of model. Choices are 'osm' or 'fmu'
        :return:
        """
        self.worker_logger.logger.info("Calling model '{}' step_sim_type '{}'".format(model_type, step_sim_type))
        arg_step_sim_value = None
        if step_sim_type == 'external_clock':
            if model_type == 'fmu':
                p = 'worker_fmu/step_fmu.py'
                # fmu needs to run with Python 2
                python = 'python'
                arg_start_datetime = start_datetime
                arg_end_datetime = end_datetime
            else:
                p = 'worker_openstudio/step_osm.py'
                python = 'python3'
                arg_start_datetime = start_datetime
                arg_end_datetime = end_datetime
        else:
            if model_type == 'fmu':
                p = 'worker_fmu/step_fmu.py'
                # fmu needs to run with Python 2
                python = 'python'
                arg_step_sim_value = step_sim_value
                arg_start_datetime = start_datetime
                arg_end_datetime = end_datetime
            else:
                p = 'worker_openstudio/step_osm.py'
                python = 'python3'
                arg_step_sim_value = step_sim_value
                arg_start_datetime = start_datetime
                arg_end_datetime = end_datetime

        if os.path.isfile(p):
            call = [
                python, p, site_id, step_sim_type, arg_start_datetime, arg_end_datetime
            ]
            if arg_step_sim_value:
                call.append('--step_sim_value={}'.format(step_sim_value))

            self.worker_logger.logger.info("Calling step_sim_type subprocess: {}".format(call))
            return_code = subprocess.call(call)

            self.check_subprocess_call(return_code, site_id, 'step_sim')
        else:
            self.worker_logger.logger.info("No file: {}".format(p))
            sys.exit(1)

        return return_code

    def run_sim_type(self, p, file_name, upload_id):
        """
        Simple wrapper for the run_sim subprocess call given the path for python file to call

        :param p: path of file to call
        :param file_name: name of file to run with extension
        :param upload_id:
        :return:
        """
        if not os.path.isfile(p):
            self.worker_logger.logger.info("No file: {}".format(p))
        else:
            return_code = subprocess.call(['python3', p, file_name, upload_id])
            self.check_subprocess_call(return_code, file_name, 'run_sim')

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
        # TODO: move the body check to before the calling of `add_site`
        body_check = self.check_message_body(message_body, 'add_site')
        if not body_check:
            self.worker_logger.logger.info(
                'message_body for add_site does not have correct keys.  Site will not be added.')
            # TODO insert sys.exit(1)?
        else:
            file_name = message_body.get('osm_name')  # TODO: change message body to file_name (for fmu)
            upload_id = message_body.get('upload_id')
            self.worker_logger.logger.info('Add site for file_name: %s, and upload_id: %s' % (file_name, upload_id))

            # TODO reorganize the message names, because now "osm_name"
            #  is misleading because we are also handling FMUs
            _, ext = os.path.splitext(file_name)
            if ext in ['.osm', '.zip']:
                p = 'worker_openstudio/add_site.py'
                self.add_site_type(p, file_name, upload_id)
            elif ext in ['.fmu']:
                p = 'worker_fmu/add_site.py'
                self.add_site_type(p, file_name, upload_id)
            else:
                self.worker_logger.logger.info(
                    "Unsupported file type: {}.  Valid extensions: .osm, .zip, .fmu".format(ext))

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
            site_rec = self.ac.mongo_db_recs.find_one({"_id": site_id})
            self.worker_logger.logger.info('Site record: {}'.format(site_rec))

            # TODO: Check if simType is defined, error if not.
            sim_type = site_rec.get("rec", {}).get("simType", "osm").replace("s:", "")
            step_sim_type, step_sim_value, start_datetime, end_datetime = self.check_step_sim_config(message_body, sim_type)
            self.worker_logger.logger.info('Start step_sim for site_id: %s, and sim_type: %s' % (site_id, sim_type))

            # TODO: do we need to have two versions of python?
            if sim_type == 'fmu':
                self.step_sim_type(site_id, step_sim_type, step_sim_value, start_datetime, end_datetime, sim_type)
            elif sim_type == 'osm':
                self.step_sim_type(site_id, step_sim_type, step_sim_value, start_datetime, end_datetime, sim_type)
            else:
                self.worker_logger.logger.info(
                    "Invalid simulation type: {}.  Only 'fmu' and 'osm' are currently supported".format(sim_type))

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
        else:
            upload_filename = message_body.get('upload_filename')
            upload_id = message_body.get('upload_id')
            self.worker_logger.logger.info(
                'Run sim for upload_filename: %s, and upload_id: %s' % (upload_filename, upload_id))

            name, ext = os.path.splitext(upload_filename)
            if ext == '.gz':
                p = 'run_sim/sim_osm/sim_osm.py'
                self.run_sim_type(p, upload_filename, upload_id)
            elif ext == '.fmu':
                p = 'run_sim/sim_fmu/sim_fmu.py'
                self.run_sim_type(p, upload_filename, upload_id)
            else:
                self.worker_logger.logger.info('Unsupported file type was uploaded')
