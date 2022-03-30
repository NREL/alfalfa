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


import os
import subprocess
import sys

from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
from alfalfa_worker.lib.logger_mixins import WorkerLoggerMixin


class WorkerJobBase(WorkerLoggerMixin, AlfalfaConnectionsBase):
    """Base class for configuration/setup of Worker Job information.

    Worker classes that inherit from this object are required to define the following:

        add_site(message_body)
        step_sim(message_body)
        run_sim(message_body)
    """

    def __init__(self):
        # inherits from AlfalfaConnectionsBase which adds in the
        # mongo, redis/sqs, s3, and other database connections.
        super().__init__()

    def _check_message_body(self, message_body, message_type):
        """
        Check that the message body contains minimum necessary keys before next step is processed.

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :param str message_type: One of 'add_site', 'step_sim', 'run_sim'
        :return:
        """
        self.logger.info("Checking message_body for: {}".format(message_type))
        self.logger.info("message_body: {}".format(message_body))
        to_return = None
        if message_type == 'add_site':
            model_name = message_body.get('model_name', False)
            upload_id = message_body.get('upload_id', False)
            to_return = False if not model_name or not upload_id else True
        elif message_type == 'step_sim':
            site_id = message_body.get('id', False)
            to_return = False if not site_id else True
        elif message_type == 'run_sim':
            upload_filename = message_body.get('upload_filename', False)
            upload_id = message_body.get('upload_id', False)
            to_return = False if not upload_filename or not upload_id else True
        return (to_return)

    def _check_subprocess_call(self, rc, file_name, message_type):
        """
        Simple wrapper to check and log subprocess calls

        :param rc: return code as returned by subprocess.call() method
        :param file_name:
        :return:
        """
        if rc == 0:
            self.logger.info("{} successful for: {}".format(message_type, file_name))
        else:
            self.logger.info("{} unsuccessful for: {}".format(message_type, file_name))
            self.logger.info("{} return code: {}".format(message_type, rc))

    def _call_subprocess(self, python, p, args):
        if os.path.isfile(p):
            return_code = subprocess.call([python, p] + args)
        else:
            self.logger.info("No file: {}".format(p))
            sys.exit(1)
        return return_code

    def add_site(self, message_body):
        """
        Caller to add a site depending on the type of file to upload.
        Valid file extensions include: '.zip'
        '.zip' file extensions expected for OpenStudio workflow directories.
        Site is added by spinning off a subprocess
        TODO: Document expected directory structure for OS workflows

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :return:
        """
        # TODO: move the body check to before the calling of `add_site`
        body_check = self._check_message_body(message_body, 'add_site')
        if not body_check:
            self.logger.info(
                'message_body for add_site does not have correct keys.  Site will not be added.')
            # TODO insert sys.exit(1)?
        else:
            file_name = message_body.get('model_name')
            upload_id = message_body.get('upload_id')
            self.logger.info('Add site for file_name: %s, and upload_id: %s' % (file_name, upload_id))

            self._call_add_site_process(file_name, upload_id)

    def _call_add_site_process(self, file_name, upload_id):
        """
        Simple wrapper for the add_site subprocess call given the path for python file to call

        :param file_name: name of file to add with extension, excludes full path
        :param upload_id:
        :return:
        """
        raise NotImplementedError

    def step_sim(self, message_body):
        """
        Caller to step through a simulation.
        Valid simulation types include: '.fmu', '.osm'
        The simulation will not be started if an invalid simulation config is provided.
        Run occurs by spinning of a subprocess.

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :return:
        """
        body_check = self._check_message_body(message_body, 'step_sim')
        if not body_check:
            self.logger.info(
                'message_body for step_sim does not have correct keys.  Simulation will not be stepped through.')
            # TODO insert sys.exit(1)?
        else:
            site_id = message_body.get('id')
            site_rec = self.mongo_db_recs.find_one({"_id": site_id})
            self.logger.info('Site record: {}'.format(site_rec))

            step_sim_type, step_sim_value, start_datetime, end_datetime = self._check_step_sim_config(message_body)
            self.logger.info('Start step_sim for site_id: %s' % (site_id))

            self._call_step_sim_process(site_id, step_sim_type, step_sim_value, start_datetime, end_datetime)

    def _call_step_sim_process(self, site_id, step_sim_type, step_sim_value, start_datetime, end_datetime):
        """
        Simple wrapper for the run_sim subprocess call given the path for python file to call

        :param p: path of file to call
        :param file_name: name of file to run with extension
        :param upload_id:
        :return:
        """
        raise NotImplementedError

    def _check_step_sim_config(self, message_body):
        """
        Check that the configuration parameters sent in the message for step_sim are valid.
        Message body must have exactly one of:
            - realtime.  expect 'true', 'false' or none provided
            - timescale.  expect int(), str that can be cast as an int, or none provided
            - external_clock. expect 'true', 'false', or none provided

        start_datetime str : formatted as "%Y-%m-%d %H:%M:%S"
        end_datetime str : formatted as "%Y-%m-%d %H:%M:%S"
        step_sim_type str : one of 'realtime', 'timescale', 'external_clock'
        step_sim_val str : one of 'true' or 'int' where int is a castable integer

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :return: step_sim_type, step_sim_value, start_datetime, end_datetime
        """
        raise NotImplementedError

    def _check_step_sim_time_config(self, message_body, start, end):
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
        self.logger.info(
            "start_datetime type: {}\tstart_datetime: {}".format(type(start_datetime), start_datetime))
        self.logger.info(
            "end_datetime type: {}\tend_datetime: {}".format(type(end_datetime), end_datetime))
        self.logger.info("realtime type: {}\trealtime: {}".format(type(realtime), realtime))
        self.logger.info("timescale type: {}\ttimescale: {}".format(type(timescale), timescale))
        self.logger.info(
            "external_clock type: {}\texternal_clock: {}".format(type(external_clock), external_clock))
        # Only want one of: realtime, timescale, or external_clock.  Else, reject configuration.
        # if (realtime and timescale) or (realtime and external_clock) or (timescale and external_clock):
        #    self.logger.info(
        #        "Only one of 'external_clock', 'timescale', or 'realtime' should be specified in message")
        #    sys.exit(1)

        # Check for at least one of the required parameters
        if not realtime and not timescale and not external_clock:
            # TODO: If exiting, what logging type to use?
            self.logger.info(
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
                self.logger.info(f"timescale: {timescale} must be an integer value")
                sys.exit(1)

        return (step_sim_type, step_sim_value, start_datetime, end_datetime)

    def run_sim(self, message_body):
        """
        Run a simulation.  Running a simulation provides vanilla run of an OSM.  Doesn't
        allow for external interfacing into model during runtime - simply runs the model.  Run occurs
        by spinning off a subprocess.

        :param message_body: Body of a single message from a boto3 Queue resource
        :type message_body: dict
        :return:
        """
        body_check = self._check_message_body(message_body, 'run_sim')
        if not body_check:
            self.logger.info(
                'message_body for step_sim does not have correct keys.  Simulation will not be run.')
        else:
            upload_filename = message_body.get('upload_filename')
            upload_id = message_body.get('upload_id')
            self.logger.info(
                'Run sim for upload_filename: %s, and upload_id: %s' % (upload_filename, upload_id))

            self._call_run_sim_process(upload_filename, upload_id)

    def _call_run_sim_process(self, file_name, upload_id):
        """
        Simple wrapper for the run_sim subprocess call given the path for python file to call

        :param file_name: name of file to run with extension
        :param upload_id:
        :return:
        """
        raise NotImplementedError

    # TODO: change name to start... since it is starting the queue watching. Run is used in this
    # project to run a simulation.
