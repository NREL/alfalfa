print("Starting Alfalfa Worker")

import os
import sys
import traceback

# Determine which worker to load based on the QUEUE.
# This may be temporary for now, not sure on how else
# to determine which worker gets launched
if 'local-queue1' in os.environ.get('JOB_QUEUE_URL', None):
    from alfalfa_worker.worker_openstudio.worker import WorkerOpenStudio as Worker
elif 'local-queue2' in os.environ.get('JOB_QUEUE_URL', None):
    from alfalfa_worker.worker_fmu.worker import WorkerFmu as Worker
else:
    print(f"Unknown queue in env var of JOB_QUEUE_URL with {os.environ.get('JOB_QUEUE_URL', None)}")

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
