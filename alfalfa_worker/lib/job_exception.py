class JobException(Exception):
    pass


class JobExceptionMessageHandler(JobException):
    """Thrown when there is an exception that occurs in an message handler.
    This is caught and reported back to the caller via redis."""


class JobExceptionInvalidModel(JobException):
    """Thrown when working on a model.
    ex: missing osw"""


class JobExceptionInvalidRun(JobException):
    """Thrown when working on run.
    ex. run does not have necessary files"""


class JobExceptionExternalProcess(JobException):
    """Thrown when an external process throws an error.
    ex. E+ can't run idf"""


class JobExceptionFailedValidation(JobException):
    """Thrown when the job fails validation for any reason.
    ex. file that should have been generated was not"""


class JobExceptionSimulation(JobException):
    """Thrown when there is a simulation issue.
    ex. Simulation falls too far behind in timescale run"""


class JobExceptionTimeout(JobException):
    """Thrown when a timeout is triggered in the job"""
