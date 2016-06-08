"""Global test fixtures."""

import uuid

import pytest

from s3keyring.s3 import S3Keyring
from s3keyring.settings import config
from keyring.errors import PasswordDeleteError


@pytest.fixture
def keyring(scope="module"):
    config.boto_config.activate_profile("test")
    return S3Keyring()


@pytest.yield_fixture
def random_entry(keyring, scope="function"):
    service = str(uuid.uuid4())
    user = str(uuid.uuid4())
    pwd = str(uuid.uuid4())
    yield (service, user, pwd)
    # Cleanup
    try:
        keyring.delete_password(service, user)
    except PasswordDeleteError as err:
        if 'not found' not in err.args[0]:
            # It's ok if the entry has been already deleted
            raise
