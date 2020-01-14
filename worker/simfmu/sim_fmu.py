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
import os
import glob
import boto3
import tarfile
import shutil
import time
from pymongo import MongoClient
import sys
import subprocess
import logging
import re
from datetime import date, datetime, timedelta
import pytz
import calendar
import traceback
from dateutil.parser import parse
from pyfmi import load_fmu
import copy
import common.testcase

try:
    s3 = boto3.resource('s3', region_name=os.environ['REGION'], endpoint_url=os.environ['S3_URL'])

    # Mongo Database
    mongo_client = MongoClient(os.environ['MONGO_URL'])
    mongodb = mongo_client[os.environ['MONGO_DB_NAME']]
    sims = mongodb.sims

    upload_file_name = sys.argv[1]
    upload_id = sys.argv[2]

    key = "uploads/%s/%s" % (upload_id, upload_file_name)
    directory = os.path.join('/simulate', upload_id)
    rootname = os.path.splitext(upload_file_name)[0]
    downloadpath = os.path.join(directory, upload_file_name)

    if not os.path.exists(directory):
        os.makedirs(directory)

    bucket = s3.Bucket(os.environ['S3_BUCKET'])
    bucket.download_file(key, downloadpath)

    sims.update_one({"_id": upload_id}, {"$set": {"simStatus": "Running"}}, False)

    # Load fmu
    config = {
        'fmupath': downloadpath,
        'step': 60
    }

    tc = common.testcase.TestCase(config)

    u = {}
    while tc.start_time < 10000:
        tc.advance(u)

    # shutil.rmtree(directory)

    time = str(datetime.now(tz=pytz.UTC))
    sims.update_one({"_id": upload_id}, {"$set": {"simStatus": "Complete", "timeCompleted": time, "s3Key": ''}}, False)

except Exception as e:
    print('runFMU: %s' % e, file=sys.stderr)
