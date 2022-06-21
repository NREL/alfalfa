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

import json
import os
import traceback
from importlib import import_module
from pathlib import Path
from typing import Dict

# Currently this is a child of WorkerJobBase, but mostly for the
# alfalfa connections. WorkerJobBase could/should be updated to inherit
# from a new class that just handles the alfalfa connections, then
# the WorkerJobBase and Dispatcher can both inherit from the new class.
from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
from alfalfa_worker.lib.job import Job, JobStatus
from alfalfa_worker.lib.logger_mixins import DispatcherLoggerMixin
from alfalfa_worker.lib.run_manager import RunManager


class Dispatcher(DispatcherLoggerMixin, AlfalfaConnectionsBase):
    """Class to pop data off a queue and determine to where the work needs
    to go. Alfalfa works off a single queue and the work is identified
    based on the payload that is in the queue (model_name).

    This class is currently designed to do the work on the worker that it is
    attached to. That is, the Dispatcher is not designed to pop work off the
    queue and submit the job to another worker with the requisite files.
    """

    def __init__(self, workdir: Path):
        super().__init__()
        self.logger.info(f"Job queue url is {self.sqs_queue}")

        self.workdir = workdir
        if not Path.exists(self.workdir):
            self.workdir.mkdir()
        self.run_manager = RunManager(self.workdir)

    def process_message(self, message):
        """Process a single message from Queue.
        message structure:
        {
            "job": "{job_name}",
            "params": {
                "{param1}": {param1_val},
                ...
            }
        }
        """
        try:
            message_body = json.loads(message.body)
            self.logger.info(message_body)
            message.delete()
            job = message_body.get('job')
            if job:
                params = message_body.get('params', {})
                self.start_job(job, params)

        except Exception as e:
            tb = traceback.format_exc()
            self.logger.error("Exception while processing message: {} with {}".format(e, tb))

    def run(self):
        """Listen to queue and process messages upon arrival
        """
        self.logger.info("Entering dispatcher run")
        while True:
            # WaitTimeSeconds triggers long polling that will wait for events to enter queue
            # Receive Message
            try:
                messages = self.sqs_queue.receive_messages(MaxNumberOfMessages=1, WaitTimeSeconds=20)
                if len(messages) > 0:
                    message = messages[0]
                    self.logger.info('Message Received with payload: %s' % message.body)
                    # Process Message
                    self.process_message(message)
            except BaseException as e:
                tb = traceback.format_exc()
                self.logger.info("Exception caught in dispatcher.run: {} with {}".format(e, tb))

    def start_job(self, job_name, parameters) -> JobStatus:
        """Start job by Python class path"""
        # Now that we aren't running as subprocesses we need this
        # because mlep likes to chdir into a directory which is then deleted
        os.chdir(self.workdir)

        job = self.create_job(job_name, parameters)
        job.start()
        return job

    def create_job(self, job_name, parameters: Dict = {}) -> Job:
        """Create a job by python class path"""
        class_ = self.find_class(job_name)
        parameters['run_manager'] = self.run_manager
        return class_(**parameters)

    @staticmethod
    def find_class(path):
        """Gets class from class path"""
        components = path.split('.')
        module = import_module('.'.join(components[:-1]))
        klazz = getattr(module, components[-1])
        return klazz

    @staticmethod
    def print_job(job_name):
        klazz = Dispatcher.find_class(job_name)
        print(f"Name: \t{klazz.__name__}")
        print(f"Description: \t{klazz.__doc__}")
        print("Message Handlers:")
        for attr_name in dir(klazz):
            attr = getattr(klazz, attr_name)
            if hasattr(attr, 'message_handler'):
                print(f"{attr.__name__}: \t {attr.__doc__}")

    @staticmethod
    def get_jobs():
        return Job.jobs.copy()
