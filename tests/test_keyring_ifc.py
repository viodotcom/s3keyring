#!/usr/bin/env python
# -*- coding: utf-8 -*-

from keyring.tests.test_backend import BackendBasicTests
from keyring.tests.py30compat import unittest
from s3keyring import s3


class S3PlaintextKeychainTestCase(BackendBasicTests, unittest.TestCase):
    def init_keyring(self):
        return s3.S3Keyring()
