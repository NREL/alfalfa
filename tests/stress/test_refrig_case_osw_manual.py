import datetime
import os
import tempfile
import zipfile
from time import sleep
from unittest import TestCase

import pytest
from alfalfa_client.alfalfa_client import AlfalfaClient


# Consider factoring this out of the test file
def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def create_zip(model_dir):
    osw_dir_path = os.path.join(os.path.dirname(__file__), 'models', model_dir)
    zip_file_fd, zip_file_path = tempfile.mkstemp(suffix='.zip')

    zipf = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
    zipdir(osw_dir_path, zipf)
    zipf.close()
    return zip_file_path


# Can't inherit TestCase as parametrize doesn't work.  We just want to run a bunch of models using pytest so okay for
# this use case
class TestRefrigCaseOSW:


    def test_simple_internal_clock(self):
        zip_file_path = create_zip('refrig_case_osw')
        alfalfa = AlfalfaClient(url='http://localhost')
        print("submit model")
        model_id = alfalfa.submit(zip_file_path)
        print("submited model")
        print(model_id)
        alfalfa.wait(model_id, "Stopped")

        alfalfa.start(
            model_id,
            external_clock="false",
            start_datetime=datetime.datetime(2019, 1, 2, 0, 0, 0),
            end_datetime=datetime.datetime(2019, 1, 30, 0, 0, 0),
            timescale=50
        )

        print(model_id)
        alfalfa.wait(model_id, "Running")
        alfalfa.stop(model_id)
        alfalfa.wait(model_id, "Stopped")


if __name__ == "__main__":
   newtest = TestRefrigCaseOSW() 

   newtest.test_simple_internal_clock()
