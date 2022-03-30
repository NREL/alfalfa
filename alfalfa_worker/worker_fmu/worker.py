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

from alfalfa_worker.worker_job_base import WorkerJobBase


class WorkerFmu(WorkerJobBase):
    """The Alfalfa alfalfa_worker class.  Used for processing messages
    from the boto3 SQS Queue resource"""

    def __init__(self):
        super().__init__()

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

        start = "0"
        end = str(60 * 60 * 24 * 365)

        (step_sim_type, step_sim_value, start_datetime, end_datetime) = self._check_step_sim_time_config(message_body, start, end)

        return (step_sim_type, step_sim_value, start_datetime, end_datetime)

    def _call_step_sim_process(self, site_id, step_sim_type, step_sim_value, start_datetime, end_datetime):
        """Simple wrapper for the step_sim subprocess call given required params

        :param p:
        :param site_id:
        :param step_sim_type:
        :param step_sim_value:
        :param start_datetime:
        :param end_datetime:
        :return:
        """
        self.logger.info("Calling model '{}' step_sim_type 'fmu'".format(step_sim_type))
        arg_step_sim_value = None

        p = 'alfalfa_worker/worker_fmu/step_fmu.py'
        # fmu needs to run with Python 2
        python = 'python3'
        arg_start_datetime = start_datetime
        arg_end_datetime = end_datetime
        if step_sim_type != 'external_clock':
            arg_step_sim_value = step_sim_value

        args = [site_id, step_sim_type, arg_start_datetime, arg_end_datetime]
        if arg_step_sim_value:
            args.append('--step_sim_value={}'.format(step_sim_value))
        self.logger.info("Calling step_sim_type subprocess: {}".format([python, p] + args))
        return_code = self._call_subprocess(python, p, args)
        self._check_subprocess_call(return_code, site_id, 'step_sim')

        return return_code

    def _call_run_sim_process(self, file_name, upload_id):
        """
        Simple wrapper for the run_sim subprocess call given the path for python file to call

        :param file_name: name of file to run with extension
        :param upload_id:
        :return:
        """
        p = 'run_sim/sim_fmu/sim_fmu.py'
        return_code = self._call_subprocess('python3', p, [file_name, upload_id])
        self._check_subprocess_call(return_code, file_name, 'run_sim')

    def _call_add_site_process(self, file_name, upload_id):
        """
        Simple wrapper for the add_site subprocess call given the path for python file to call

        :param file_name: name of file to add with extension, excludes full path
        :param upload_id:
        :return:
        """
        p = 'alfalfa_worker/worker_fmu/add_site.py'
        return_code = self._call_subprocess('python3', p, [file_name, upload_id])
        self._check_subprocess_call(return_code, file_name, 'add_site')
