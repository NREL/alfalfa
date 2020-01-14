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
import sys
import os
import glob
import boto3
import json
import tarfile
import zipfile
import shutil
import time
from subprocess import call
import logging
import common

(osw_zip_name, upload_id, directory) = common.precheck_argus(sys.argv)

logger = logging.getLogger('addsite')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log_file = os.path.join(directory, 'addsite.log')
fh = logging.FileHandler(log_file)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])

# First download the osw and run the workflow to get an osm file
key = "uploads/%s/%s" % (upload_id, osw_zip_name)
osw_zip_path = os.path.join(directory, 'in.zip')

bucket = s3.Bucket(os.environ['S3_BUCKET'])
bucket.download_file(key, osw_zip_path)

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

call(['openstudio', 'run', '-m', '-w', oswpath])

# Now take the osm produced by the osw and run
# it through another workflow to generate tags

seedpath = os.path.join(directory, 'seed.osm')
epwpath = os.path.join(directory, 'workflow/files/weather.epw')
workflowpath = os.path.join(directory, 'workflow/workflow.osw')
points_jsonpath = os.path.join(directory, 'workflow/reports/haystack_report_haystack.json')
mapping_jsonpath = os.path.join(directory, 'workflow/reports/haystack_report_mapping.json')

tar = tarfile.open("workflow.tar.gz")
tar.extractall(directory)
tar.close()

shutil.copyfile(osmpath, seedpath)
shutil.copyfile(user_epwpath, epwpath)

call(['openstudio', 'run', '-m', '-w', workflowpath])

common.make_ids_unique(upload_id, points_jsonpath, mapping_jsonpath)
common.replace_siteid(upload_id, points_jsonpath, mapping_jsonpath)

common.upload_site_DB_Cloud(points_jsonpath, bucket, directory)

shutil.rmtree(directory)
