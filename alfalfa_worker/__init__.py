# from .alfalfa_worker import AlfalfaConnections

# -*- coding: utf-8 -*-
from pkg_resources import get_distribution, DistributionNotFound

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = 'alfalfa-alfalfa_worker'
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound

# Not sure that these are needed here. Leave for now...
__all__ = ['add_site',
           'lib',
           'run_sim',
           'step_sim']
