#!/usr/bin/env python
# -*- coding: utf-8 -*-


import configparser
import shutil
import os
import s3keyring
from s3keyring.exceptions import ProfileNotFoundError


class Config:
    def __init__(self, config_file=None):

        if config_file is None:
            # The default config file is ~/.s3keyring.ini
            config_file = os.path.join(os.path.expanduser('~'),
                                       '.s3keyring.ini')

        if not os.path.isfile(config_file):
            shutil.copyfile(s3keyring.__default_config_file__, config_file)

        self.config = configparser.ConfigParser()
        self.config_file = config_file
        self.load()

    def load(self):
        """Load configuration from ini file"""
        self.config.read(self.config_file)

    def save(self):
        """Save configuration to ini file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
            # Force flushing the file to disk
            f.flush()
            os.fsync(f.fileno())

    def get(self, section, param):
        """Get configuration option"""
        val = self.config.get(section, param)
        if val != '':
            return val

    def get_profile(self, profile_name):
        """Returns a dict-like object with profile options"""
        section = "profile:{}".format(profile_name)
        if not self.config.has_section(section):
            raise ProfileNotFoundError(
                "Profile {} not found".format(profile_name))
        return dict(self.config.items(section))

    def remove_profile(self, profile_name):
        """Removes a profile, if it exists. Otherwise does nothing."""
        removed = self.config.remove_section("profile:{}".format(profile_name))
        if removed:
            self.save()

    def get_from_profile(self, profile_name, param):
        """Reads a config option for a profile"""
        return self.get("profile:{}".format(profile_name), param)

    def initialize_profile(self, profile_name):
        """Initializes a profile in the config file"""
        self.config.add_section("profile:{}".format(profile_name))

    def set(self, section, param, value):
        """Writes a configuration parameter"""
        if not self.config.has_section(section):
            self.config.add_section(section)

        if value is None:
            value = ''
        self.config.set(section, param, value)
        self.save()

    def set_in_profile(self, profile_name, param, value):
        """Writes a profile parameter value"""
        self.set("profile:{}".format(profile_name), param, value)
