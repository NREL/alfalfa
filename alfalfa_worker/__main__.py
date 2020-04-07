print("Starting Alfalfa Worker")

import sys
from alfalfa_worker.worker import Worker

if __name__ == '__main__':
    try:
        worker = Worker()
        worker.worker_logger.logger.info("Worker initialized")
    except BaseException:  # TODO: what exceptions to catch?
        print('Exception while starting up alfalfa_worker', file=sys.stderr)
        sys.exit(1)

    try:
        worker.run()  # run the alfalfa_worker
    except BaseException:  # TODO: what exceptions to catch?
        print('Exception while running alfalfa_worker', file=sys.stderr)
