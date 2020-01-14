'''
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

'''

import json
import sys
import os
from subprocess import call
import tarfile


def upload_site_DB_Cloud(jsonpath, bucket, folderpath):
    '''
    Purpose: upload the tagged site to the database and cloud
    Inputs: the S3-bucket
    Returns: nothing
    '''
    # get the id of site tag(remove the 'r:')
    site_ref = ''
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
        tar.add(folderpath, filter=reset, arcname=site_ref)
        tar.close()

        # This upload the tagged site to the cloud
        bucket.upload_file(tarname, "parsed/%s" % tarname)

        # os.remove(tarname)
