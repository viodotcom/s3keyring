#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Tests the specific functionality of the s3keyring which is not part of the
# keyring interface.


import pytest
import uuid
from s3keyring.s3 import S3Keyring, InitError


@pytest.fixture
def keyring(scope='module'):
    """Default keyring, using the default profile"""
    kr = S3Keyring()
    kr.configure(ask=False)
    return kr


@pytest.yield_fixture
def profile(keyring, scope='module'):
    """A dummy keyring profile which is just a clone of the default"""
    profile_config = dict(keyring.config.get_profile('test'))
    profile_tuple = (str(uuid.uuid4()), profile_config)
    yield profile_tuple


@pytest.fixture
def profile_keyring(profile, scope='module'):
    """A keyring that uses a non-default profile"""
    kr = S3Keyring(profile=profile[1], profile_name=profile[0])
    return kr


class TestS3():
    def test_wrong_keyring_initialization(self, profile):
        """Tests that a wrong initialization raises an exception"""
        with pytest.raises(InitError):
            S3Keyring(profile=profile[1])

    def test_configure_profile_with_envars(self, profile, monkeypatch):
        """Configures an additional profile"""
        monkeypatch.setenv('KEYRING_BUCKET', profile[1]['bucket'])
        monkeypatch.setenv('KEYRING_KMS_KEY_ID', profile[1]['kms_key_id'])
        monkeypatch.setenv('KEYRING_NAMESPACE', profile[1]['namespace'])
        kr = S3Keyring(profile_name=profile[0])
        kr.configure(ask=False)
        # The default profile should not have been modified
        assert kr.config.get_from_profile('default', 'bucket') != \
            profile[1]['bucket']
        # And the new profile should have been created in the ini config file
        assert kr.config.get_from_profile(profile[0], 'bucket') == \
            profile[1]['bucket']
        assert kr.config.get_from_profile(profile[0], 'kms_key_id') == \
            profile[1]['kms_key_id']
        assert kr.config.get_from_profile(profile[0], 'namespace') == \
            profile[1]['namespace']
