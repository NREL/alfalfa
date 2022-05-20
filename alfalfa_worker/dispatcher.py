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
import uuid
from importlib import import_module
from pathlib import Path

from alfalfa_worker.jobs import openstudio
# Currently this is a child of WorkerJobBase, but mostly for the
# alfalfa connections. WorkerJobBase could/should be updated to inherit
# from a new class that just handles the alfalfa connections, then
# the WorkerJobBase and Dispatcher can both inherit from the new class.
from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
from alfalfa_worker.lib.job import Job
from alfalfa_worker.lib.logger_mixins import DispatcherLoggerMixin
from alfalfa_worker.lib.run_manager import RunManager
from alfalfa_worker.worker_fmu.worker import WorkerFmu
# Workers that are defined in this dispatcher
from alfalfa_worker.worker_openstudio.worker import WorkerOpenStudio


class Dispatcher(DispatcherLoggerMixin, AlfalfaConnectionsBase):
    """Class to pop data off a queue and determine to where the work needs
    to go. Alfalfa works off a single queue and the work is identified
    based on the payload that is in the queue (model_name).

    This class is currently designed to do the work on the worker that it is
    attached to. That is, the Dispatcher is not designed to pop work off the
    queue and submit the job to another worker with the requisite files.
    """

    def __init__(self):
        super().__init__()
        self.logger.info(f"Job queue url is {self.sqs_queue}")

        # create classes for the workers that this dispatcher supports
        self.worker_openstudio_class = WorkerOpenStudio()
        self.worker_fmu_class = WorkerFmu()
        self.workdir = '/runs'
        if not os.path.exists(self.workdir):
            os.mkdir(self.workdir)
        self.run_manager = RunManager(self.workdir)

    def determine_worker_class(self, test_str):
        """This is the only place where we should decide
        if the work is an OSW or an FMU
        """
        worker_class = None
        test_str = test_str.lower().replace('.', '')
        if test_str in ['osw', 'osm', 'zip']:
            worker_class = self.worker_openstudio_class
        elif test_str == 'fmu':
            worker_class = self.worker_fmu_class

        if worker_class is None:
            raise Exception(f"Unable to determine worker class of string {test_str}")

        return worker_class

    def process_message(self, message):
        """Process a single message from Queue.  Depending on operation requested,
        will call one of:

            - step_sim
            - add_site
            - run_sim
        """
        try:
            message_body = json.loads(message.body)
            self.logger.info(message_body)
            message.delete()
            op = message_body.get('op')
            if op == 'InvokeAction':
                action = message_body.get('action')
                if action in ['init', 'addSite']:
                    # get the model type from the body to determine which class will
                    # dispatch the work
                    model_name = Path(message_body.get('model_name'))

                    worker_class = self.determine_worker_class(model_name.suffix)
                    self.logger.info(f"Dispatching {action} with model_type {model_name.suffix} to worker {worker_class}")
                    if action == 'init':
                        # For testing purposes, just return the
                        # worker class that was assigned
                        return worker_class
                    elif action == 'addSite':
                        if worker_class.__class__ is WorkerOpenStudio:
                            self.start_job(openstudio.CreateRun.job_path(),
                                           {'model_name': message_body.get('model_name'),
                                            'upload_id': message_body.get('upload_id')})
                            self.logger.info("add site job has completed")
                        else:
                            self.start_job("alfalfa_worker.jobs.modelica.CreateRun",
                                           {'model_name': message_body.get('model_name'),
                                            'upload_id': message_body.get('upload_id')})
                elif action in ['runSite', 'runSim']:
                    # get the site ID out of the message
                    site_id = message_body.get('id')
                    site_rec = self.mongo_db_recs.find_one({"_id": site_id})
                    sim_type = site_rec.get("rec", {}).get("simType").replace("s:", "")

                    worker_class = self.determine_worker_class(sim_type)
                    self.logger.info(f"Dispatching {action} with sim_type {sim_type} to worker {worker_class}")
                    if action == 'runSite':
                        params = {'run_id': message_body.get('id'),
                                  'realtime': message_body.get('realtime'),
                                  'timescale': message_body.get('timescale'),
                                  'external_clock': message_body.get('externalClock'),
                                  'start_datetime': message_body.get('startDatetime'),
                                  'end_datetime': message_body.get('endDatetime')}
                        if worker_class.__class__ is WorkerOpenStudio:
                            self.start_job(openstudio.StepRun.job_path(), params)
                        else:
                            self.start_job('alfalfa_worker.jobs.modelica.StepRun', params)
                    elif action == 'runSim':
                        worker_class.run_sim(message_body)

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

    def start_job(self, job_name, parameters):
        """Start job in thread by Python class path"""
        klazz = self.find_class(job_name)
        job_id = str(uuid.uuid4())
        job_dir = os.path.join(self.workdir, job_id)
        os.mkdir(job_dir)
        parameters['working_dir'] = job_dir
        parameters['run_manager'] = self.run_manager
        job = klazz(**parameters)
        job.start()
        return job_id

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
