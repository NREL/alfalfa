########################################################################################################################
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

import glob
import os
import shutil
import sys
import tarfile
import zipfile
from subprocess import call

# Local
from alfalfa_worker.add_site.add_site_logger import AddSiteLogger
from alfalfa_worker.lib import precheck_argus, make_ids_unique, replace_siteid, upload_site_to_filestore, \
    alfalfa_connections

(osw_zip_name, upload_id, directory) = precheck_argus(sys.argv)

ac = alfalfa_connections.AlfalfaConnections()
add_site_logger = AddSiteLogger(directory)

# First download the osw and run the workflow to get an osm file
key = "uploads/%s/%s" % (upload_id, osw_zip_name)
osw_zip_path = os.path.join(directory, 'in.zip')

ac.download_file(key, osw_zip_path)

zzip = zipfile.ZipFile(osw_zip_path)
zzip.extractall(directory)

osws = glob.glob(("%s/**/*.osw" % directory), recursive=True)
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

seedpath = os.path.join(directory, 'seed.osm')
epwpath = os.path.join(directory, 'workflow/files/weather.epw')
workflowpath = os.path.join(directory, 'workflow/workflow.osw')
points_jsonpath = os.path.join(directory, 'workflow/reports/haystack_report_haystack.json')
mapping_jsonpath = os.path.join(directory, 'workflow/reports/haystack_report_mapping.json')

# Extract workflow tarball into this directory
tar = tarfile.open("workflow.tar.gz")
tar.extractall(directory)
tar.close()

# Copy .osm into seed.osm
shutil.copyfile(osmpath, seedpath)

# Copy epw file into weather.epw
shutil.copyfile(user_epwpath, epwpath)

# Rerun model through workflow for alfalfa specific workflow
call(['openstudio', 'run', '-m', '-w', workflowpath])

# TODO: Why exactly are the following two needed?
make_ids_unique(upload_id, points_jsonpath, mapping_jsonpath)
replace_siteid(upload_id, points_jsonpath, mapping_jsonpath)

# Upload the files back to filestore and clean local directory
upload_site_to_filestore(points_jsonpath, ac.bucket, directory)
shutil.rmtree(directory)
