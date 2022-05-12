
from datetime import datetime

import pytz

from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
from alfalfa_worker.lib.job import Job
from alfalfa_worker.lib.testcase import TestCase


class FullRun(AlfalfaConnectionsBase, Job):

    def __init__(self, run_id) -> None:
        self.run = self.checkout_run(run_id)

    def exec(self) -> None:
        self.mongo_db_sims.update_one({"_id": self.run.id}, {"$set": {"simStatus": "Running"}}, False)

        # Load fmu
        config = {
            'fmupath': self.run.join('model.fmu'),
            'step': 60
        }

        tc = TestCase(config)

        u = {}
        while tc.start_time < 10000:
            tc.advance(u)

        time = str(datetime.now(tz=pytz.UTC))
        self.mongo_db_sims.update_one({"_id": self.run.id}, {"$set": {"simStatus": "Complete", "timeCompleted": time, "s3Key": f"run/{self.run.id}.tar.gz"}}, False)

        self.stop()
