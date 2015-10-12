# -*- coding: utf-8 -*-

import s3keyring
import os


def test_read_config():
    """Reads the dummyparam from default section"""
    assert s3keyring.read_config('default', 'dummyparam') == 'dummyvalue'
    assert os.path.isfile(os.path.join(os.path.expanduser('~'),
                                       '.s3keyring.ini'))


def test_write_config():
    """Sets value for an existing configuration option"""
    orig_value = s3keyring.read_config('default', 'dummyparam')
    s3keyring.write_config('default', 'dummyparam', 'anothervalue')
    assert s3keyring.read_config('default', 'dummyparam') == 'anothervalue'
    s3keyring.write_config('default', 'dummyparam', orig_value)
