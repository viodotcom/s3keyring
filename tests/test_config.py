# -*- coding: utf-8 -*-

import s3keyring


def test_write_read_config():
    """Sets value for an existing configuration option"""
    orig_value = s3keyring.read_config('default', 'dummyparam')
    s3keyring.write_config('default', 'dummyparam', 'anothervalue')
    assert s3keyring.read_config('default', 'dummyparam') == 'anothervalue'
    s3keyring.write_config('default', 'dummyparam', orig_value)
