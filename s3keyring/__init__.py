# -*- coding: utf-8 -*-
"""Keeps your secrets safe in S3"""

from s3keyring import metadata
import os
import inspect


__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright

__dir__ = os.path.dirname(inspect.getfile(inspect.currentframe()))
__default_config_file__ = os.path.join(__dir__, 's3keyring.ini')
