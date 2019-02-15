'''
Copyright: See the link for details: http://github.com/ibpsa/project1-boptest/blob/master/license.md
BOPTEST. Copyright (c) 2018 International Building Performance Simulation Association (IBPSA) and contributors. All rights reserved.
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
'''

from __future__ import print_function
import os
import sys


def precheck_argus(argu_vars):

    if len(argu_vars) == 3:
        model_name = argu_vars[1]
        upload_id = argu_vars[2]
    else:
        print('addSite called with incorrect number of arguments: %s.' % len(argu_vars), file=sys.stderr)
        sys.exit(1)

    if not upload_id:
        print('upload_id is empty', file=sys.stderr)
        sys.exit(1)

    folderpath_cloud = os.path.join('/parse', upload_id)

    try:
        if not os.path.exists(folderpath_cloud):
            os.makedirs(folderpath_cloud)
    except:
        print('error making add site parsing directory for upload_id: %s' % upload_id, file=sys.stderr)
        sys.exit(1)

    return (model_name, upload_id, folderpath_cloud)

