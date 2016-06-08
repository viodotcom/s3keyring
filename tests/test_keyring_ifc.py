"""Test keyring module interface."""

import logging
import unittest

from keyring.tests.test_backend import BackendBasicTests
from s3keyring import s3
from s3keyring.settings import config


logging.getLogger().setLevel("ERROR")


class S3PlaintextKeychainTestCase(BackendBasicTests, unittest.TestCase):
    def init_keyring(self):
        config.boto_config.activate_profile("test")
        return s3.S3Keyring()
