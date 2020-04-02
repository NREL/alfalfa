from __future__ import print_function

import glob
import boto3
import lib
import zipfile
import os
import shutil
import sys
import tarfile
from subprocess import call

# Local
from alfalfa_worker.add_site.add_site_logger import AddSiteLogger
from alfalfa_worker.lib import precheck_argus, make_ids_unique, replace_siteid, upload_site_to_filestore, \
    alfalfa_connections


class AddSite:
    """A wrapper class around adding sites"""

    def __init__(self):

        """Are we able to define:
                - upload_ID
                - directory
                - ac
            at the class level or do all of these have unique values to each funciton"""

        # add_osm variables
        (self.osm_name, self.osm_upload_id, self.osm_directory) = precheck_argus(sys.argv)
        self.osm_key = "uploads/%s/%s" % (self.upload_id, self.osm_name)

        # add_osw varaibles
        (self.osw_zip_name, self.osw_upload_id, self.osw_directory) = precheck_argus(sys.argv)
        self.osw_key = "uploads/%s/%s" % (self.osw_upload_id, self.osw_zip_name)

        # add_fmu varibales
        (self.fmu_upload_name, self.fmu_upload_id, self.fmu_directory) = lib.precheck_argus(sys.argv)
        self.fmu_key = "uploads/%s/%s" % (self.fmu_upload_id, self.fmu_upload_name)
        self.s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])

        # Seemingly Shared variables
        self.ac = alfalfa_connections.AlfalfaConnections()

    def add_osm(self):

        # download osm from filestore. rename to seed.osm
        # key = "uploads/%s/%s" % (upload_id, osm_name)
        seedpath = os.path.join(self.osm_directory, 'seed.osm')
        self.ac.bucket.download_file(self.osm_key, seedpath)

        # Extract workflow tarball into this directory
        tar = tarfile.open("workflow.tar.gz")
        tar.extractall(self.osm_directory)
        tar.close()

        workflowpath = os.path.join(self.osm_directory, 'workflow/workflow.osw')
        points_jsonpath = os.path.join(self.osm_directory, 'workflow/reports/haystack_report_haystack.json')
        mapping_jsonpath = os.path.join(self.osm_directory, 'workflow/reports/haystack_report_mapping.json')
        call(['openstudio', 'run', '-m', '-w', workflowpath])

        # TODO: Why exactly are the following two needed?
        make_ids_unique(self.osm_upload_id, points_jsonpath, mapping_jsonpath)
        replace_siteid(self.osm_upload_id, points_jsonpath, mapping_jsonpath)

        # Upload the files back to filestore and clean local directory
        upload_site_to_filestore(points_jsonpath, self.ac.bucket, self.osm_directory)
        shutil.rmtree(self.osm_directory)

    def add_osw(self):

        # (osw_zip_name, upload_id, directory) = precheck_argus(sys.argv)
        #
        # ac = alfalfa_connections.AlfalfaConnections()
        # add_site_logger = AddSiteLogger(directory)

        # First download the osw and run the workflow to get an osm file
        # key = "uploads/%s/%s" % (upload_id, osw_zip_name)
        osw_zip_path = os.path.join(self.osw_directory, 'in.zip')

        self.ac.download_file(self.osw_key, osw_zip_path)

        zzip = zipfile.ZipFile(osw_zip_path)
        zzip.extractall(self.osw_directory)

        osws = glob.glob(("%s/**/*.osw" % self.osw_directory), recursive=True)
        if osws:
            oswpath = osws[0]
            oswdir = os.path.dirname(oswpath)
            # this is where the new osm will be after we run the workflow
            osmpath = os.path.join(oswdir, 'run/in.osm')
            epws = glob.glob(("%s/files/*.epw" % oswdir), recursive=True)
            if epws:
                user_epwpath = epws[0]
        else:
            sys.exit(1)

        # Run initial workflow from zip file
        call(['openstudio', 'run', '-m', '-w', oswpath])

        # Now take the osm produced by the osw and run
        # it through another workflow to generate tags

        seedpath = os.path.join(self.osw_directory, 'seed.osm')
        epwpath = os.path.join(self.osw_directory, 'workflow/files/weather.epw')
        workflowpath = os.path.join(self.osw_directory, 'workflow/workflow.osw')
        points_jsonpath = os.path.join(self.osw_directory, 'workflow/reports/haystack_report_haystack.json')
        mapping_jsonpath = os.path.join(self.osw_directory, 'workflow/reports/haystack_report_mapping.json')

        # Extract workflow tarball into this directory
        tar = tarfile.open("workflow.tar.gz")
        tar.extractall(self.osw_directory)
        tar.close()

        # Copy .osm into seed.osm
        shutil.copyfile(osmpath, seedpath)

        # Copy epw file into weather.epw
        shutil.copyfile(user_epwpath, epwpath)

        # Rerun model through workflow for alfalfa specific workflow
        call(['openstudio', 'run', '-m', '-w', workflowpath])

        # TODO: Why exactly are the following two needed?
        make_ids_unique(self.osw_upload_id, points_jsonpath, mapping_jsonpath)
        replace_siteid(self.osw_upload_id, points_jsonpath, mapping_jsonpath)

        # Upload the files back to filestore and clean local directory
        upload_site_to_filestore(points_jsonpath, self.ac.bucket, self.osw_directory)
        shutil.rmtree(self.osw_directory)

    def add_fmu(self):

        # fmu files gets uploaded with user defined names, but here we rename
        # to model.fmu to avoid keeping track of the (unreliable, non unique) user upload name
        # createFMUTags will however use the original fmu upload name for the display name of the site
        fmupath = os.path.join(self.fmu_directory, 'model.fmu')
        jsonpath = os.path.join(self.fmu_directory, 'tags.json')

        bucket = self.s3.Bucket(os.environ['S3_BUCKET'])
        bucket.download_file(self.fmu_key, fmupath)

        call(['python', 'add_site/add_fmu/create_tags.py', fmupath, self.fmu_upload_name, jsonpath])

        lib.upload_site_to_filestore(jsonpath, bucket, self.fmu_directory)

        shutil.rmtree(self.fmu_directory)
