import os
import sys
from datetime import datetime


def process_datetime_string(dt, logger=None):
    """
    Check that datetime string has been correctly passed.
    Should be passed as: "%Y-%m-%d %H:%M:%S"

    :param str dt: datetime string
    :return: formatted time string
    """
    try:
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        return (dt.strftime("%Y-%m-%d %H:%M:%S"))
    except ValueError:
        if logger:
            logger.info("Invalid datetime string passed: {}".format(dt))
        sys.exit(1)


def rel_symlink(src, dst):
    """
    Create a symlink to a file (src),
    where the link (dst) is a relative path,
    relative to the given src
    """
    src = os.path.relpath(src, os.path.dirname(dst))
    os.symlink(src, dst)
