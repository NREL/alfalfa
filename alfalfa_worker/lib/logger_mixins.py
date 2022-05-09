from __future__ import print_function

import logging
import os


class LoggerMixinBase(object):
    """Base class for the logger mixins. All loggers will have the same formatting,
    writing to both a file and the stream.

    Inherit from this class to configure the logger and filenames"""

    def __init__(self, logger_name, *args, **kwargs) -> None:
        # Need to call parent since this is a mixin
        super().__init__(*args, **kwargs)

        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
        self.logger = logging.getLogger(logger_name)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        self.fh = logging.FileHandler(f"{logger_name}.log")
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)

        self.sh = logging.StreamHandler()
        self.sh.setFormatter(self.formatter)
        self.logger.addHandler(self.sh)


class DispatcherLoggerMixin(LoggerMixinBase):
    """A logger specific for the tasks of the Dispatcher"""

    def __init__(self, *args, **kwargs):
        super().__init__('alfalfa_dispatcher', *args, **kwargs)


class WorkerLoggerMixin(LoggerMixinBase):
    """A logger specific for the tasks of the Worker"""

    def __init__(self, *args, **kwargs):
        super().__init__('alfalfa_worker', *args, **kwargs)


class AddSiteLoggerMixin(LoggerMixinBase):
    """A logger specific for the tasks of adding a site"""

    def __init__(self, *args, **kwargs):
        super().__init__('add_site', *args, **kwargs)


class RunManagerLoggerMixin(LoggerMixinBase):
    """A logger specific for the tasks of adding a site"""

    def __init__(self, *args, **kwargs):
        super().__init__('add_site', *args, **kwargs)


class ModelLoggerMixin(object):
    """A logger specific for the tasks of the ModelAdvancer, does not stream"""

    def __init__(self, *args, **kwargs):
        # Need to call parent since this is a mixin
        super().__init__(*args, **kwargs)

        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
        self.logger = logging.getLogger('simulation')
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.fh = logging.FileHandler('simulation.log')
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)
