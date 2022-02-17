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

import traceback
import logging
import os
import json

from pathlib import Path

# Currently this is a child of WorkerJobBase, but mostly for the
# alfalfa connections. WorkerJobBase could/should be updated to inherit
# from a new class that just handles the alfalfa connections, then
# the WorkerJobBase and Dispatcher can both inherit from the new class.
from alfalfa_worker.lib.alfalfa_connections import AlfalfaConnectionsBase

# Workers that are defined in this dispatcher
from alfalfa_worker.worker_openstudio.worker import WorkerOpenStudio
from alfalfa_worker.worker_fmu.worker import WorkerFmu


class DispatcherLoggerMixin:
    """A logger specific for the tasks of the Dispatcher.
    Feel free to move this to its own file!"""

    def __init__(self, *args, **kwargs):
        # Since this is a mixin, call all other parent class initializers
        super().__init__(*args, **kwargs)

        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
        self.logger = logging.getLogger('alfalfa_dispatcher')
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.fh = logging.FileHandler('alfalfa_dispatcher.log')
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)

        self.sh = logging.StreamHandler()
        self.sh.setFormatter(self.formatter)
        self.logger.addHandler(self.sh)


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

                # get the model type from the body to determine which class will
                # dispatch the work
                model_name = Path(message_body.get('model_name'))

                # This is the only place where we should decide
                # if the work is an OSW or an FMU
                if model_name.suffix.lower() == '.osw':
                    worker_class = self.worker_openstudio_class
                elif model_name.suffix.lower() == '.zip':
                    worker_class = self.worker_openstudio_class
                elif model_name.suffix.lower() == '.fmu':
                    worker_class = self.worker_fmu_class

                if action == 'init':
                    # For testing purposes, just return the
                    # worker class that was assigned
                    return worker_class

                # TODO change to step_sim
                if action == 'runSite':
                    # TODO: Strongly type the step_sim, add_site, and run_sim (add mypy???)
                    worker_class.step_sim(message_body)

                # TODO change to add_site
                elif action == 'addSite':
                    worker_class.add_site(message_body)

                # TODO change to run_sim
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
