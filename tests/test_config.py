# -*- coding: utf-8 -*-


import pytest
from s3keyring.s3 import S3Keyring


@pytest.fixture
def config(scope='module'):
    return S3Keyring().config


def test_read_config(config):
    """Sets value for an existing configuration option"""
    profile_name = config.get('default', 'profile')
    assert profile_name == 'default'


def test_write_config(config):
    config.set('default', 'dummyparam', 'anothervalue')
    config.save()
    config.load()
    assert config.get('default', 'dummyparam') == 'anothervalue'
