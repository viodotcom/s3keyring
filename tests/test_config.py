# -*- coding: utf-8 -*-


import pytest
import uuid
import tempfile
import os
from s3keyring.s3 import S3Keyring


@pytest.fixture
def config(scope='module'):
    return S3Keyring(profile_name='test').config


@pytest.yield_fixture
def dummyparam(config, scope='module'):
    yield 'dummyparam'
    config.config.remove_option('default', 'dummyparam')


@pytest.yield_fixture
def dummy_config_file():
    filename = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    yield filename
    if os.path.isfile(filename):
        os.remove(filename)


@pytest.fixture
def custom_config_file(dummy_config_file, scope='module'):
    return S3Keyring(profile_name='test', config_file=dummy_config_file).config


def test_read_config(config):
    """Sets value for an existing configuration option"""
    profile_name = config.get('default', 'profile')
    assert profile_name == 'default'


def test_write_config(config, dummyparam):
    dummyvalue = str(uuid.uuid4())
    config.set('default', dummyparam, dummyvalue)
    config.save()
    config.load()
    assert config.get('default', dummyparam) == dummyvalue


def test_read_custom_config_file(custom_config_file, dummy_config_file):
    """Reads a parameter from a custom config file"""
    profile_name = custom_config_file.get('default', 'profile')
    assert profile_name == 'default'
    assert custom_config_file.config_file == dummy_config_file
    assert os.path.isfile(dummy_config_file)


def test_write_config_in_custom_config_file(custom_config_file, dummyparam,
                                            config):
    dummyvalue = str(uuid.uuid4())
    custom_config_file.set('default', dummyparam, dummyvalue)
    custom_config_file.save()
    custom_config_file.load()
    assert custom_config_file.get('default', dummyparam) == dummyvalue
    assert config.config_file != custom_config_file.config_file
    config.load()
    assert config.get('default', dummyparam) != dummyvalue
