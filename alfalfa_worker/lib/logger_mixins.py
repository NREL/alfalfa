from __future__ import print_function

import logging


class LoggerMixinBase(object):
    """Base class for the logger mixins. All loggers will have the same formatting,
    writing to both a file and the stream.

    Inherit from this class to configure the logger and filenames"""

    def __init__(self, logger_name, *args, **kwargs) -> None:
        # Need to call parent since this is a mixin
        super().__init__(*args, **kwargs)

        self.logger = logging.getLogger(logger_name)
        self.fh = logging.FileHandler(f"{logger_name}.log")
        self.logger.addHandler(self.fh)


class DispatcherLoggerMixin(LoggerMixinBase):
    """A logger specific for the tasks of the Dispatcher"""

    def __init__(self, *args, **kwargs):
        super().__init__('alfalfa_dispatcher', *args, **kwargs)
