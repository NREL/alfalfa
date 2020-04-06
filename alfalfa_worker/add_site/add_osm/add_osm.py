########################################################################################################################
#
#  Copyright (c) 2008-2018, Alliance for Sustainable Energy, LLC, and other contributors. All rights reserved.
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


import os
import shutil
import sys
import tarfile
from subprocess import call


# Local
from alfalfa_worker.add_site.add_site_logger import AddSiteLogger
from alfalfa_worker.lib import precheck_argus, make_ids_unique, replace_siteid
from alfalfa_worker.lib.alfalfa_connections import AlfalfaConnections


def add_osm(osm_name, upload_id, directory, ac, add_site_logger):
    # download osm from filestore. rename to seed.osm
    key = "uploads/%s/%s" % (upload_id, osm_name)
    seedpath = os.path.join(directory, 'seed.osm')
    ac.bucket.download_file(key, seedpath)

    # Extract workflow tarball into this directory
    tar = tarfile.open("workflow.tar.gz")
    tar.extractall(directory)
    tar.close()

    workflowpath = os.path.join(directory, 'workflow/workflow.osw')
    points_jsonpath = os.path.join(directory, 'workflow/reports/haystack_report_haystack.json')
    mapping_jsonpath = os.path.join(directory, 'workflow/reports/haystack_report_mapping.json')
    call(['openstudio', 'run', '-m', '-w', workflowpath])

    # TODO: Why exactly are the following two needed?
    make_ids_unique(upload_id, points_jsonpath, mapping_jsonpath)
    replace_siteid(upload_id, points_jsonpath, mapping_jsonpath)

    # Upload the files back to filestore and clean local directory
    # upload_site_to_filestore(points_jsonpath, ac.bucket, directory)
    ac.upload_site_to_filestore(points_jsonpath, directory)
    shutil.rmtree(directory)


if __name__ == "__main__":
    (osm_name, upload_id, directory) = precheck_argus(sys.argv)
    ac = AlfalfaConnections()
    add_site_logger = AddSiteLogger(directory)

    add_osm(osm_name, upload_id, directory, ac, add_site_logger)
