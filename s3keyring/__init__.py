# -*- coding: utf-8 -*-
"""Keeps your secrets safe in S3"""

from s3keyring import metadata
import configparser
import shutil
import os
import inspect


__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright

__dir__ = os.path.dirname(inspect.getfile(inspect.currentframe()))
__default_config_file__ = os.path.join(__dir__, '..',
                                       's3keyring.ini')
__user_config_file__ = os.path.join(os.path.expanduser('~'),
                                    '.s3keyring.ini')


# Program configuration management
def __initialize_config():
    """Copies the default configuration to the user homedir"""
    shutil.copyfile(__default_config_file__, __user_config_file__)


def __get_config():
    """Gets a ConfigParser object with the current program configuration"""
    if not os.path.isfile(__user_config_file__):
        __initialize_config()

    cp = configparser.ConfigParser()
    cp.read(__user_config_file__)
    return cp


def read_config(section, param):
    """Reads a configuration parameter"""
    return __get_config().get(section, param)


def write_config(section, param, value):
    """Writes a configuration parameter"""
    cfg = __get_config()
    if not cfg.has_section(section):
        cfg.add_section(section)

    cfg.set(section, param, value)
    with open(__user_config_file__, 'w') as f:
        cfg.write(f)
