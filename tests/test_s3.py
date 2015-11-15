#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Tests the specific functionality of the s3keyring which is not part of the
# keyring interface.


import pytest
import s3keyring
from s3keyring.s3 import S3Keyring, supported, InitError


@pytest.fixture
def default_keyring(scope='module'):
    """Default keyring, using the default profile"""
    kr = S3Keyring()
    kr.configure(ask=False)
    return kr


@pytest.fixture
def profile(scope='module'):
    """A dummy keyring profile which is just a clone of the default"""
    return dict(s3keyring.read_profile('default'))


@pytest.fixture
def profile_keyring(profile, scope='module'):
    """A keyring that uses a non-default profile"""
    kr = S3Keyring(profile=profile, profile_name='dummy')
    return kr


class TestS3():
    pytestmark = pytest.mark.skipif(
        not supported(), reason="S3 backend not supported or not configured")

    def test_wrong_keyring_initialization(self, profile):
        """Tests that a wrong initialization raises an exception"""
        with pytest.raises(InitError):
            S3Keyring(profile=profile)
