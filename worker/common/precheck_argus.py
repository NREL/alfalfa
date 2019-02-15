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


