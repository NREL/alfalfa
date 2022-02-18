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

from __future__ import print_function

import glob
import os
import shutil
import sys
import zipfile
from subprocess import call
import json

# Local
from alfalfa_worker.add_site_logger import AddSiteLogger
from alfalfa_worker.lib.precheck_argus import precheck_argus
from alfalfa_worker.lib.tagutils import make_ids_unique, replace_site_id
from alfalfa_worker.lib.alfalfa_connections import AlfalfaConnectionsBase


def rel_symlink(src, dst):
    """
    Create a symlink to a file (src),
    where the link (dst) is a relative path,
    relative to the given src
    """
    src = os.path.relpath(src, os.path.dirname(dst))
    os.symlink(src, dst)


class AddSite(AlfalfaConnectionsBase):
    """A wrapper class around adding sites"""

    def __init__(self, fn, up_id, f_dir):
        """
        Initialize.
        :param fn: name of file to submit
        :param up_id: upload_id as first created by Upload.js when sending file to file s3 bucket (addSiteResolver)
        :param f_dir: directory to upload to on s3 bucket after parsing: parsed/{site_id}/.  Also used locally during this process.
        """
        super().__init__()

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
        if self.file_ext == '.zip':
            self.add_osw()
        elif self.file_ext == '.fmu':
            self.add_fmu()
        else:
            self.add_site_logger.logger.error("Unsupported file extension: {}".format(self.file_ext))
            os.exit(1)

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

    def insert_fmu_tags(self, points_json_path):
        with open(points_json_path, 'r') as f:
            data = f.read()
        points_json = json.loads(data)

        self.add_site_to_mongo(points_json, self.upload_id)

    def insert_os_tags(self, points_json_path, mapping_json_path):
        """
        Make unique ids and replace site_id.  Upload to mongo and filestore.
        :return:
        """
        # load mapping and points json files generated by previous workflow
        with open(points_json_path, 'r') as f:
            data = f.read()
        points_json = json.loads(data)

        with open(mapping_json_path, 'r') as f:
            data = f.read()
        mapping_json = json.loads(data)

        # fixup tags
        # This is important to avoid duplicates in the case when a client submits the same model
        # more than one time
        points_json, mapping_json = make_ids_unique(points_json, mapping_json)
        points_json = replace_site_id(self.upload_id, points_json)

        # save "fixed up" json
        with open(points_json_path, 'w') as fp:
            json.dump(points_json, fp)

        with open(mapping_json_path, 'w') as fp:
            json.dump(mapping_json, fp)

        # add points to database
        self.add_site_to_mongo(points_json, self.upload_id)

    def add_osw(self):
        """
        Workflow for osw.
        This function must merge the "built in" haystack workflow measures with
        the user measure, and then run the resulting combined workflow
        :return:
        """
        self.add_site_logger.logger.info("add_osw for {}".format(self.key))

        # download and extract the payload
        payload_dir = os.path.join(self.bucket_parsed_site_id_dir, 'payload/')
        os.mkdir(payload_dir)
        payload_file_path = os.path.join(payload_dir, 'in.zip')
        self.s3_bucket.download_file(self.key, payload_file_path)
        zzip = zipfile.ZipFile(payload_file_path)
        workflow_dir = os.path.join(self.bucket_parsed_site_id_dir, 'workflow/')
        zzip.extractall(workflow_dir)

        osws = glob.glob(("%s/**/*.osw" % workflow_dir), recursive=True)
        if osws:
            # there is only support for one osw at this time
            submitted_osw_path = osws[0]
            submitted_workflow_path = os.path.dirname(submitted_osw_path)
        else:
            sys.exit(1)

        # locate the "default" workflow
        default_workflow_path = '/alfalfa/alfalfa_worker/worker_openstudio/lib/workflow/workflow.osw'

        # Merge the default workflow measures into the user submitted workflow
        call(['openstudio', '/alfalfa/alfalfa_worker/worker_openstudio/lib/merge_osws.rb', default_workflow_path, submitted_osw_path])

        # run workflow
        call(['openstudio', 'run', '-m', '-w', submitted_osw_path])

        points_json_path = os.path.join(submitted_workflow_path, 'reports/haystack_report_haystack.json')
        mapping_json_path = os.path.join(submitted_workflow_path, 'reports/haystack_report_mapping.json')
        self.insert_os_tags(points_json_path, mapping_json_path)

        # create a "simulation" directory that has everything required for simulation
        simulation_dir = os.path.join(self.bucket_parsed_site_id_dir, 'simulation/')
        os.mkdir(simulation_dir)

        idf_src_path = os.path.join(submitted_workflow_path, 'run/in.idf')
        idf_dest_path = os.path.join(simulation_dir, 'sim.idf')
        rel_symlink(idf_src_path, idf_dest_path)

        haystack_src_path = os.path.join(submitted_workflow_path, 'reports/haystack_report_mapping.json')
        haystack_dest_path = os.path.join(simulation_dir, 'haystack_report_mapping.json')
        rel_symlink(haystack_src_path, haystack_dest_path)

        haystack_src_path = os.path.join(submitted_workflow_path, 'reports/haystack_report_haystack.json')
        haystack_dest_path = os.path.join(simulation_dir, 'haystack_report_haystack.json')
        rel_symlink(haystack_src_path, haystack_dest_path)

        variables_src_path = os.path.join(submitted_workflow_path, 'reports/export_bcvtb_report_variables.cfg')
        variables_dest_path = os.path.join(simulation_dir, 'variables.cfg')
        rel_symlink(variables_src_path, variables_dest_path)

        # variables.cfg also needs to be located next to the idf to satisfy EnergyPlus conventions
        idf_src_dir = os.path.dirname(idf_src_path)
        variables_ep_path = os.path.join(idf_src_dir, 'variables.cfg')
        rel_symlink(variables_src_path, variables_ep_path)

        # hack. need to find a more general approach to preserve osw resources that might be needed at simulation time
        for file in glob.glob(submitted_workflow_path + '/python/*'):
            idfdir = os.path.dirname(idf_src_path)
            filename = os.path.basename(file)
            dst = os.path.join(idfdir, filename)
            rel_symlink(file, dst)

        # find weather file (if) defined by osw and copy into simulation directory
        with open(submitted_osw_path, 'r') as osw:
            data = osw.read()
        submitted_osw = json.loads(data)

        epw_name = submitted_osw['weather_file']
        if epw_name:
            epw_src_path = self.find_file(epw_name, submitted_workflow_path)
            epw_dst_path = os.path.join(simulation_dir, 'sim.epw')
            rel_symlink(epw_src_path, epw_dst_path)

        # push entire directory to file storage
        filestore_response, output = self.add_site_to_filestore(self.bucket_parsed_site_id_dir, self.upload_id)

        # remove directory
        shutil.rmtree(self.bucket_parsed_site_id_dir)

    def find_file(self, name, path):
        for root, dirs, files in os.walk(path):
            if name in files:
                return os.path.join(root, name)

    def add_fmu(self):
        """
        Workflow for fmu.  External call to python2 must be made since currently we are using an
        old version of the Modelica Buildings Library and JModelica.
        :return:
        """
        self.add_site_logger.logger.info("add_fmu for {}".format(self.key))

        self.s3_bucket.download_file(self.key, self.fmu_path)

        # External call to python2 to create FMU tags
        call(['python', 'lib/fmu_create_tags.py', self.fmu_path, self.file_name, self.fmu_json])

        # insert tags into db
        self.insert_fmu_tags(self.fmu_json)

        # push entire directory to file storage
        filestore_response, output = self.add_site_to_filestore(self.bucket_parsed_site_id_dir, self.upload_id)

        # remove directory
        shutil.rmtree(self.bucket_parsed_site_id_dir)


if __name__ == "__main__":
    args = sys.argv
    file_name, upload_id, directory = precheck_argus(args)
    adder = AddSite(file_name, upload_id, directory)
    adder.main()
