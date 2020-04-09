from __future__ import print_function

import glob
import os
import shutil
import sys
import tarfile
import zipfile
from subprocess import call
import json

# Local
from alfalfa_worker.add_site.add_site_logger import AddSiteLogger
from alfalfa_worker.lib import precheck_argus, make_ids_unique, replace_site_id
from alfalfa_worker.lib.alfalfa_connections import AlfalfaConnections


class AddSite:
    """A wrapper class around adding sites"""

    def __init__(self, fn, up_id, f_dir):
        """
        Initialize.
        :param fn: name of file to submit
        :param up_id: upload_id as first created by Upload.js when sending file to file s3 bucket (addSiteResolver)
        :param f_dir: directory to upload to on s3 bucket after parsing: parsed/{site_id}/.  Also used locally during this process.
        """
        self.add_site_logger = AddSiteLogger()
        self.add_site_logger.logger.info("AddSite called with args: {} {} {}".format(fn, up_id, f_dir))
        self.file_name = fn
        self.upload_id = up_id
        self.bucket_parsed_site_id_dir = f_dir
        _, self.file_ext = os.path.splitext(self.file_name)
        self.key = "uploads/%s/%s" % (self.upload_id, self.file_name)

        # Define OSM and OSW specific attributes
        self.seed_osm_path = os.path.join(self.bucket_parsed_site_id_dir, 'seed.osm')
        self.workflow_osw_path = os.path.join(self.bucket_parsed_site_id_dir, 'workflow/workflow.osw')
        self.epw_path = os.path.join(self.bucket_parsed_site_id_dir, 'workflow/files/weather.epw')  # mainly only used for add_osw
        self.report_haystack_json = os.path.join(self.bucket_parsed_site_id_dir, 'workflow/reports/haystack_report_haystack.json')
        self.report_mapping_json = os.path.join(self.bucket_parsed_site_id_dir, 'workflow/reports/haystack_report_mapping.json')

        # Define FMU specific attributes
        self.fmu_path = os.path.join(self.bucket_parsed_site_id_dir, 'model.fmu')
        self.fmu_json = os.path.join(self.bucket_parsed_site_id_dir, 'tags.json')

        # Create connections
        self.ac = AlfalfaConnections()

        # Needs to be set after files are uploaded / parsed.
        self.site_ref = None

    def main(self):
        """
        Main entry point after init.  Adds site based on file ext.  Worfklow is generally as follows:
        1. Download file from s3 bucket
        2. Ingest model file and add tags
        3. Send data to mongo and s3 bucket
        4. Remove files generated during this process
        :return:
        """
        if self.file_ext == '.osm':
            self.add_osm()
        elif self.file_ext == '.zip':
            self.add_osw()
        elif self.file_ext == '.fmu':
            self.add_fmu()
        else:
            self.add_site_logger.logger.error("Unsupported file extension: {}".format(self.file_ext))
            os.exit(1)

    def extract_workflow_tar(self):
        """
        Extract workflow tarball into this directory
        :return:
        """
        tar = tarfile.open("workflow.tar.gz")
        tar.extractall(self.bucket_parsed_site_id_dir)
        tar.close()

    def get_site_ref(self, haystack_json):
        """
        Find the site given the haystack JSON file.  Remove 'r:' from string.
        :param haystack_json: json serialized Haystack document
        :return: site_ref: id of site
        """
        site_ref = ''
        with open(haystack_json) as json_file:
            data = json.load(json_file)
            for entity in data:
                if 'site' in entity:
                    if entity['site'] == 'm:':
                        site_ref = entity['id'].replace('r:', '')
                        break
        return site_ref

    def os_files_final_touches_and_upload(self):
        """
        Make unique ids and replace site_id.  Upload to mongo and filestore.
        :return:
        """
        # TODO: Why exactly are the following two needed?
        make_ids_unique(self.upload_id, self.report_haystack_json, self.report_mapping_json)
        replace_site_id(self.upload_id, self.report_haystack_json, self.report_mapping_json)

        # Upload to mongo & filestore, clean local directory
        self.add_to_mongo_and_filestore()

    def add_to_mongo_and_filestore(self):
        """
        Attempt upload to mongo and filestore.  Function exits if not uploaded correctly
        based on expected return values from methods in AlfalfaConnections.
        :return:
        """
        if self.file_ext != '.fmu':
            f = self.report_haystack_json
            self.site_ref = self.get_site_ref(self.report_haystack_json)
        else:
            f = self.fmu_json
            self.site_ref = self.get_site_ref(self.fmu_json)

        # Check mongo upload works correctly
        mongo_response = self.ac.add_site_to_mongo(f, self.site_ref)
        if len(mongo_response.inserted_ids) > 0:
            self.add_site_logger.logger.info('added {} ids to MongoDB under site_ref: {}'.format(len(mongo_response.inserted_ids), self.site_ref))
        else:
            self.add_site_logger.logger.warning('site not added to MongoDB under site_ref: {}'.format(self.site_ref))
            sys.exit(1)

        # Check filestore upload works correctly
        filestore_response, output = self.ac.add_site_to_filestore(self.bucket_parsed_site_id_dir, self.site_ref)

        # Clean local directory
        shutil.rmtree(self.bucket_parsed_site_id_dir)
        if filestore_response:
            self.add_site_logger.logger.info(
                'added to filestore: {}'.format(output))
        else:
            self.add_site_logger.logger.warning('site not added to filestore - exception: {}'.format(output))
            sys.exit(1)

    def add_osm(self):
        """
        Workflow for osm.
        :return:
        """
        self.add_site_logger.logger.info("add_osm for {}".format(self.key))
        self.ac.s3_bucket.download_file(self.key, self.seed_osm_path)

        # Extract workflow tarball into this directory
        self.extract_workflow_tar()

        # Run OS Workflow on uploaded file to apply afalfa necessary measures
        call(['openstudio', 'run', '-m', '-w', self.workflow_osw_path])

        self.os_files_final_touches_and_upload()

    def add_osw(self):
        """
        Workflow for osw.  The osm is run through 2x workflows:
        1. Original workflow defined by upload
        2. Alfalfa specific workflow
        :return:
        """
        self.add_site_logger.logger.info("add_osw for {}".format(self.key))
        osw_zip_path = os.path.join(self.bucket_parsed_site_id_dir, 'in.zip')

        self.ac.s3_bucket.download_file(self.key, osw_zip_path)

        zzip = zipfile.ZipFile(osw_zip_path)
        zzip.extractall(self.bucket_parsed_site_id_dir)

        osws = glob.glob(("%s/**/*.osw" % self.bucket_parsed_site_id_dir), recursive=True)
        if osws:
            osw_path = osws[0]
            osw_dir = os.path.dirname(osw_path)
            # this is where the new osm will be after we run the workflow
            osm_path = os.path.join(osw_dir, 'run/in.osm')
            epws = glob.glob(("%s/files/*.epw" % osw_dir), recursive=True)
            if epws:
                user_epw_path = epws[0]
        else:
            sys.exit(1)

        # Run initial workflow from zip file
        call(['openstudio', 'run', '-m', '-w', osw_path])

        # Now take the osm produced by the osw and run
        # it through another workflow to generate tags

        # Extract workflow tarball into this directory
        self.extract_workflow_tar()

        # Copy .osm into seed.osm
        shutil.copyfile(osm_path, self.seed_osm_path)

        # Copy user specified epw file into weather.epw
        shutil.copyfile(user_epw_path, self.epw_path)

        # Rerun model through workflow for alfalfa specific workflow
        call(['openstudio', 'run', '-m', '-w', self.workflow_osw_path])

        self.os_files_final_touches_and_upload()

    def add_fmu(self):
        """
        Workflow for fmu.  External call to python2 must be made since currently we are using an
        old version of the Modelica Buildings Library and JModelica.
        :return:
        """
        self.add_site_logger.logger.info("add_fmu for {}".format(self.key))

        self.ac.s3_bucket.download_file(self.key, self.fmu_path)

        # External call to python2 to create FMU tags
        call(['python', 'lib/fmu_create_tags.py', self.fmu_path, self.file_name, self.fmu_json])

        self.add_to_mongo_and_filestore()


if __name__ == "__main__":
    args = sys.argv
    file_name, upload_id, directory = precheck_argus(args)
    adder = AddSite(file_name, upload_id, directory)
    adder.main()
