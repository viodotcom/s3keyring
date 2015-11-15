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
__default_config_file__ = os.path.join(__dir__, 's3keyring.ini')
__user_config_file__ = os.path.join(os.path.expanduser('~'),
                                    '.s3keyring.ini')

if not os.path.isfile(__user_config_file__):
    shutil.copyfile(__default_config_file__, __user_config_file__)

config = configparser.ConfigParser()
config.read(__user_config_file__)


def read_config(section, param):
    """Reads a configuration parameter"""
    return config.get(section, param)


def read_profile(profile_name):
    """Returns a dict-like object with profile options"""
    return config["profile:{}".format(profile_name)]


def read_profile_config(profile_name, param):
    """Reads a config option for a profile"""
    return read_config("profile:{}".format(profile_name), param)


def write_config(section, param, value):
    """Writes a configuration parameter"""
    if not config.has_section(section):
        config.add_section(section)

    config.set(section, param, value)
    with open(__user_config_file__, 'w') as f:
        config.write(f)


def write_profile_config(profile_name, param, value):
    """Writes a profile parameter value"""
    write_config("profile:{}".format(profile_name), param, value)
