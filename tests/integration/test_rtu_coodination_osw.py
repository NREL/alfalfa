# import os
# import datetime
# import pytest
# import tempfile
# import zipfile
# from unittest import TestCase
# from alfalfa_client.alfalfa_client import AlfalfaClient


# # Consider factoring this out of the test file
# def zipdir(path, ziph):
#     # ziph is zipfile handle
#     for root, dirs, files in os.walk(path):
#         for file in files:
#             ziph.write(os.path.join(root, file))


# @pytest.mark.integration
# class TestRTUCoordinationOSW(TestCase):

#     def test_simple_internal_clock(self):
#         osw_dir_path = os.path.join(os.path.dirname(__file__), 'models', 'rtu_coordination_osw')
#         zip_file_fd, zip_file_path = tempfile.mkstemp(suffix='.zip')

#         zipf = zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED)
#         zipdir(osw_dir_path, zipf)
#         zipf.close()

#         alfalfa = AlfalfaClient(url='http://localhost')
#         model_id = alfalfa.submit(zip_file_path)

#         alfalfa.wait(model_id, "Stopped")

#         alfalfa.start(
#             model_id,
#             external_clock="false",
#             start_datetime=datetime.datetime(2019, 1, 2, 0, 0, 0),
#             end_datetime=datetime.datetime(2019, 1, 3, 0, 0, 0),
#             timescale=5
#         )

#         alfalfa.wait(model_id, "Running")
#         alfalfa.stop(model_id)
#         alfalfa.wait(model_id, "Stopped")
