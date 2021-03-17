print("Starting Alfalfa Worker")

import sys
from alfalfa_worker.worker import Worker
import traceback


if __name__ == '__main__':
    try:
        worker = Worker()
        worker.worker_logger.logger.info("Worker initialized")
    except BaseException as e:  # TODO: what exceptions to catch?
        tb = traceback.format_exc()
        print("Exception while starting up alfalfa_worker error {} with {}".format(e, tb), file=sys.stderr)
        sys.exit(1)

    try:
        worker.run()  # run the alfalfa_worker
    except BaseException as e:  # Catch all exceptions
        tb = traceback.format_exc()
        worker.worker_logger.logger.error("Uncaught worker error {} with {}".format(e, tb))
        sys.exit(1)
