import os
import sys
import traceback


def rel_symlink(src, dst):
    """
    Create a symlink to a file (src),
    where the link (dst) is a relative path,
    relative to the given src
    """
    src = os.path.relpath(src, os.path.dirname(dst))
    os.symlink(src, dst)


def exc_to_str():
    tb = traceback.format_exception(*sys.exc_info())

    return ''.join(tb)


def to_bool(value: str):
    false_strings = ["false", "no", "0"]
    true_strings = ["true", "yes", "1"]
    if isinstance(value, bool):
        return value
    elif value.lower() in false_strings:
        return False
    elif value.lower() in true_strings:
        return True
    else:
        raise ValueError(f"Invalid string \"{value}\" provided for boolean conversion")
