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
import boto3
import json
import tarfile
import shutil
import time
from subprocess import call
import logging

if len(sys.argv) == 3:
    osm_name = sys.argv[1]
    upload_id = sys.argv[2]
else:
    print('addSite called with incorrect number of arguments: %s.' % len(sys.argv), file=sys.stderr)
    sys.exit(1)

if not upload_id:
    print('upload_id is empty', file=sys.stderr)
    sys.exit(1)

directory = os.path.join('/parse', upload_id)

try:
    if not os.path.exists(directory):
        os.makedirs(directory)
except:
    print('error making add site parsing directory for upload_id: %s' % upload_id, file=sys.stderr)
    sys.exit(1)

logger = logging.getLogger('addsite')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

log_file = os.path.join(directory,'addsite.log')
fh = logging.FileHandler(log_file)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

s3 = boto3.resource('s3', region_name='us-east-1')
key = "uploads/%s/%s" % (upload_id, osm_name)
seedpath = os.path.join(directory, 'seed.osm')
workflowpath = os.path.join(directory, 'workflow/workflow.osw')
jsonpath = os.path.join(directory, 'workflow/reports/haystack_report_haystack.json')

tar = tarfile.open("workflow.tar.gz")
tar.extractall(directory)
tar.close()

#time.sleep(5)

bucket = s3.Bucket('alfalfa')
bucket.download_file(key, seedpath)

call(['openstudio', 'run', '-m', '-w', workflowpath])

site_ref = False
with open(jsonpath) as json_file:
    data = json.load(json_file)
    for entity in data:
        if 'site' in entity:
            if entity['site'] == 'm:':
                site_ref = entity['id'].replace('r:', '')
                break

if site_ref:
    # This adds a new haystack site to the database
    call(['npm', 'run', 'start', jsonpath, site_ref])

    # Open the json file and get a site reference
    # Store the results by site ref
    def reset(tarinfo):
        tarinfo.uid = tarinfo.gid = 0
        tarinfo.uname = tarinfo.gname = "root"
        return tarinfo

    tarname = "%s.tar.gz" % site_ref
    tar = tarfile.open(tarname, "w:gz")
    tar.add(directory, filter=reset, arcname=site_ref)
    tar.close()

    bucket.upload_file(tarname, "parsed/%s" % tarname)
    os.remove(tarname)

shutil.rmtree(directory)
