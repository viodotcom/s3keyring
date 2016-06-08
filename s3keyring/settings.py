"""S3Keyring settings."""

import logging
import os

import boto3facade.config
from configparser import ConfigParser


PACKAGE_PATH = os.path.abspath(os.path.dirname(__file__))


def _get_config_file():
    project_config = os.path.join(os.path.curdir, ".s3keyring.ini")
    if os.path.isfile(project_config):
        return project_config
    user_config = os.path.expanduser("~/.s3keyring.ini")
    return user_config


CONFIG_FILE = _get_config_file()


class Config(object):
    """S3 Keyring configuration."""

    LOGGER_NAME = "s3keyring"
    ENVAR_PREFIX = "S3KEYRING_"
    DEFAULT_BOTO_PROFILE = "default"
    CONFIG_FILE_TEMPLATE = os.path.join(PACKAGE_PATH, "s3keyring.ini")

    def __init__(self, section_name, config_file=CONFIG_FILE):
        if config_file:
            self.from_ini_file(config_file, section_name)

        # Configuration keys that will go to the .ini file and that the user
        # can easily customize:
        #
        # namespace: A common prefix for all keys stored in the keyring
        # kms_key_id: The ID of the KMS key used to handle encryption
        # use_local_keyring: should the local keyring be used as a fallback?

        keys = ["aws_profile", "bucket", "kms_key_id", "namespace",
                "use_local_keyring"]

        self.boto_config = boto3facade.config.Config(
            env_prefix=self.ENVAR_PREFIX,
            config_file=config_file,
            config_file_template=self.CONFIG_FILE_TEMPLATE,
            active_profile=self.DEFAULT_BOTO_PROFILE,
            keys=keys,
            required_keys=keys[:3],
            logger=logging.getLogger(self.LOGGER_NAME),
            fallback={
                "aws_profile": "default",
                "namespace": "default",
                "use_local_keyring": "yes"})

    @property
    def profile(self):
        """A shortcut to boto_config.profile."""
        return self.boto_config.profile

    def from_ini_file(self, config_file, section_name):
        """Load configuration overrides from :data:`CONFIG_FILE`.

        :param section_name: Name of the section in the ``*.ini`` file to load.
        """
        parser = ConfigParser()
        parser.read(config_file)
        if parser.has_section(section_name):
            for name, value in parser.items(section_name):
                setattr(self, name.upper(), value)


config = Config('default')
