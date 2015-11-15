# -*- coding: utf-8 -*-

import s3keyring


def test_read_config():
    """Sets value for an existing configuration option"""
    profile_name = s3keyring.read_config('default', 'profile')
    assert profile_name == 'default'


def test_write_config():
    s3keyring.write_config('default', 'dummyparam', 'anothervalue')
    assert s3keyring.read_config('default', 'dummyparam') == 'anothervalue'
