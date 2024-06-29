import logging
import os
import sys
import traceback
from pathlib import Path

logging.info("Starting Alfalfa Dispatcher")

# Determine which worker to load based on the QUEUE.
# This may be temporary for now, not sure on how else
# to determine which worker gets launched
from alfalfa_worker.dispatcher import Dispatcher

if __name__ == '__main__':
    try:
        workdir = Path(os.environ.get('RUN_DIR', '/runs'))
        dispatcher = Dispatcher(workdir)
        dispatcher.logger.info("Dispatcher initialized")
    except BaseException as e:  # TODO: what exceptions to catch?
        tb = traceback.format_exc()
        print("Exception while starting up alfalfa dispatcher. Error {} with {}".format(e, tb), file=sys.stderr)
        sys.exit(1)

    try:
        dispatcher.run()  # run the dispatcher
    except BaseException as e:  # Catch all exceptions
        tb = traceback.format_exc()
        dispatcher.logger.error("Uncaught worker error {} with {}".format(e, tb))
        sys.exit(1)
