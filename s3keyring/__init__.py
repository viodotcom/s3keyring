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


class ProfileNotFoundError(Exception):
    pass


class Config:
    def __init__(self):
        self.config_file = os.path.join(os.path.expanduser('~'),
                                        '.s3keyring.ini')
        if not os.path.isfile(self.config_file):
            shutil.copyfile(__default_config_file__, self.config_file)
        self.config = configparser.ConfigParser()
        self.load()

    def load(self):
        """Load configuration from ini file"""
        self.config.read(self.config_file)

    def save(self):
        """Save configuration to ini file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get(self, section, param):
        """Get configuration option"""
        return self.config.get(section, param)

    def get_profile(self, profile_name):
        """Returns a dict-like object with profile options"""
        section = "profile:{}".format(profile_name)
        if section not in self.config:
            raise ProfileNotFoundError(
                "Profile {} not found".format(profile_name))
        return self.config[section]

    def get_from_profile(self, profile_name, param):
        """Reads a config option for a profile"""
        return self.read_config("profile:{}".format(profile_name), param)

    def initialize_profile(self, profile_name):
        """Initializes a profile in the config file"""
        self.config.add_section("profile:{}".format(profile_name))

    def set(self, section, param, value):
        """Writes a configuration parameter"""
        if not self.config.has_section(section):
            self.config.add_section(section)

        self.config.set(section, param, value)
        self.save()

    def set_in_profile(self, profile_name, param, value):
        """Writes a profile parameter value"""
        self.set("profile:{}".format(profile_name), param, value)
