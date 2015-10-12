#!/usr/bin/env python
# -*- coding: utf-8 -*-

from keyring.tests.test_backend import BackendBasicTests
from keyring.tests.py30compat import unittest
from s3keyring import S3


@unittest.skipUnless(S3.supported(),
                     "You need to configure the AWS credentials")
class S3PlaintextKeychainTestCase(BackendBasicTests, unittest.TestCase):
    def init_keyring(self):
        return S3.S3Keyring()
