# -*- coding: utf-8 -*-


import pytest
import uuid
from s3keyring.s3 import S3Keyring


@pytest.fixture
def config(scope='module'):
    return S3Keyring(profile_name='test').config


@pytest.yield_fixture
def dummyparam(config, scope='module'):
    yield 'dummyparam'
    config.config.remove_option('default', 'dummyparam')


@pytest.fixture
def dummyvalue():
    return str(uuid.uuid4())


def test_read_config(config):
    """Sets value for an existing configuration option"""
    profile_name = config.get('default', 'profile')
    assert profile_name == 'default'


def test_write_config(config, dummyparam, dummyvalue):
    config.set('default', dummyparam, dummyvalue)
    config.save()
    config.load()
    assert config.get('default', dummyparam) == dummyvalue
