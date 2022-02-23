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

import json
import os
import shutil
import sys
from subprocess import call

from alfalfa_worker.lib.alfalfa_connections_base import AlfalfaConnectionsBase
# Local
from alfalfa_worker.lib.logger_mixins import AddSiteLoggerMixin
from alfalfa_worker.lib.precheck_argus import precheck_argus
from alfalfa_worker.lib.tagutils import make_ids_unique, replace_site_id


def rel_symlink(src, dst):
    """
    Create a symlink to a file (src),
    where the link (dst) is a relative path,
    relative to the given src
    """
    src = os.path.relpath(src, os.path.dirname(dst))
    os.symlink(src, dst)


class AddSite(AddSiteLoggerMixin, AlfalfaConnectionsBase):
    """A wrapper class around adding sites"""

    def __init__(self, fn, up_id, f_dir):
        """
        Initialize.
        :param fn: name of file to submit
        :param up_id: upload_id as first created by Upload.js when sending file to file s3 bucket (addSiteResolver)
        :param f_dir: directory to upload to on s3 bucket after parsing: parsed/{site_id}/.  Also used locally during this process.
        """
        # TODO: replace super call with just super() when this is moved to Python3!
        super().__init__()

        self.logger.info("AddSite called with args: {} {} {}".format(fn, up_id, f_dir))
        self.file_name = fn
        self.upload_id = up_id
        self.bucket_parsed_site_id_dir = f_dir
        _, self.file_ext = os.path.splitext(self.file_name)
        self.key = "uploads/%s/%s" % (self.upload_id, self.file_name)

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
        self.add_fmu()

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
        self.logger.info("add_fmu for {}".format(self.key))

        self.s3_bucket.download_file(self.key, self.fmu_path)

        # External call to python2 to create FMU tags
        call(['python', 'alfalfa_worker/lib/fmu_create_tags.py', self.fmu_path, self.file_name, self.fmu_json])

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
