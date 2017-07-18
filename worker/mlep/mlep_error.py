# -*- coding: utf-8 -*-

"""
Error
~~~~~~~~~~~~~~~
This module contains the custom error classes for mlep

:author: Willy Bernal Heredia
:copyright: The Alliance for Sustainable Energy
:license: BSD-3
"""


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
