#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import base64
import logging

from keyring.errors import (PasswordDeleteError)
from keyring.backend import KeyringBackend
from botocore.exceptions import EndpointConnectionError
import boto3facade.s3
import string
import six
import keyring
import sys

from s3keyring.settings import config

# Python2/3 compatibility
if sys.version_info.major == 2:
    from base64 import decodestring as base64_decode
    from base64 import encodestring as base64_encode
elif sys.version_info.major == 3:
    from base64 import decodebytes as base64_decode
    from base64 import encodebytes as base64_encode
else:
    raise Exception("Invalid Python major version: {}".format(sys.version_info.major))


LEGAL_CHARS = (
    getattr(string, 'letters', None)     # Python 2.x
    or getattr(string, 'ascii_letters')  # Python 3.x
    ) + string.digits + '/_-'

ESCAPE_FMT = "_{}02X"

logger = logging.getLogger()
logger.setLevel("INFO")


class PasswordGetError(Exception):
    """Raised when there is an error retrieving a password.
    """
    pass


class InitError(Exception):
    """Raised when the S3 backend has not been properly initialized
    """
    pass


class S3Backed(object):
    def __init__(self, config_file=None):
        """Initialize the keyring."""

        if config_file:
            config.boto_config.config_file = config_file
            config.boto_config.load()

        self.s3 = boto3facade.s3.S3(config=config.boto_config)

    @property
    def bucket(self):
        return self.s3.resource.Bucket(config.profile["bucket"])

    def supported(self):
        try:
            resp = self.s3.client.list_objects(Bucket=self.bucket.name)
            return resp['ResponseMetadata']['HTTPStatusCode'] == 200
        except:
            return False

    @property
    def kms_key_id(self):
        return config.profile["kms_key_id"]

    @property
    def use_local_keyring(self):
        return config.profile.get("use_local_keyring", "no") == 'yes'

    @property
    def namespace(self):
        """A namespace is simply a shared S3 prefix across a set of keys."""
        try:
            return _escape_for_s3(config.profile["namespace"])
        except KeyError:
            logger.error("No keyring namespace was found: did you run "
                         "`s3keyring configure`?")


class S3Keyring(S3Backed, KeyringBackend):
    """
    BaseS3Keyring is a S3-based implementation of keyring.
    This keyring stores the password directly in S3 and provides methods
    which may be overridden by subclasses to support
    encryption and decryption. The encrypted payload is stored in base64
    format.
    """

    def _get_s3_key(self, service, username):
        """The S3 key where the secret will be stored."""
        return "{}/{}/{}/secret.b64".format(self.namespace, service, username)

    def _get_service_prefix(self, service):
        """Get the S3 prefix for a given service."""
        return "{}/{}".format(self.namespace, service)

    def get_value(self, *args, **kwargs):
        """An alias of method get_password"""
        return self.get_password(*args, **kwargs)

    def list_keys(self, service):
        """List the keys associated to a given service."""
        prefix = self._get_service_prefix(service)
        return [x.key[len(prefix)+1:-11] for x
                in list(self.bucket.objects.filter(Prefix=prefix))]

    def get_password(self, service, username):
        """Read the password from the S3 bucket."""
        service = _escape_for_s3(service)
        username = _escape_for_s3(username)

        # Read the password from S3
        prefix = self._get_s3_key(service, username)
        try:
            values = list(self.bucket.objects.filter(Prefix=prefix))
        except EndpointConnectionError:
            if self.use_local_keyring:
                # Can't connect to S3: fallback to the local keyring
                print("WARNING: can't connect to S3, using OS keyring instead",
                      file=sys.stderr)
                return keyring.get_password(service, username)
            else:
                raise

        if len(values) == 0:
            # service/username not found
            return
        if len(values) > 1:
            msg = "Ambiguous prefix {prefix} in bucket {bucket}.".format(
                prefix=prefix, bucket=self.bucket.name)
            raise PasswordGetError(msg)
        pwd_base64 = values[0].get()['Body'].read()
        pwd = base64_decode(pwd_base64)
        return pwd.decode('utf-8')

    def set_value(self, *args, **kwargs):
        """An alias for method set_password."""
        return self.set_password(*args, **kwargs)

    def set_password(self, service, username, password):
        """Write the password in the S3 bucket."""
        service = _escape_for_s3(service)
        username = _escape_for_s3(username)

        pwd_base64 = base64_encode(password.encode('utf-8')).decode()

        # Save in S3 using both server and client side encryption
        keyname = self._get_s3_key(service, username)
        try:
            self.bucket.Object(keyname).put(ACL='private', Body=pwd_base64,
                                            ServerSideEncryption='aws:kms',
                                            SSEKMSKeyId=self.kms_key_id)
        except EndpointConnectionError:
            if self.use_local_keyring:
                # Can't connect to S3: fallback to OS keyring
                print("WARNING: can't connect to S3, storing in OS keyring",
                      file=sys.stderr)
                keyring.set_password(service, username, password)
            else:
                raise

    def delete_value(self, *args, **kwargs):
        """An alias for delete_password."""
        return self.delete_password(*args, **kwargs)

    def delete_password(self, service, username):
        """Delete the password for the username of the service."""
        service = _escape_for_s3(service)
        username = _escape_for_s3(username)
        prefix = self._get_s3_key(service, username)
        try:
            objects = list(self.bucket.objects.filter(Prefix=prefix))
            if len(objects) == 0:
                msg = ("Password for {service}/{username} not found"
                       ).format(service=service, username=username)
                raise PasswordDeleteError(msg)
            elif len(objects) > 1:
                msg = ("Multiple objects in bucket {bucket} match the prefix "
                       "{prefix}.").format(bucket=self.bucket.name,
                                           prefix=prefix)
            else:
                objects[0].delete()
        except EndpointConnectionError:
            if self.use_local_keyring:
                # Can't connect to S3: fallback to OS keyring
                print("WARNING: can't connect to S3, deleting from OS keyring",
                      file=sys.stderr)
            else:
                raise

        # Delete also in the local keyring
        if self.use_local_keyring:
            try:
                keyring.delete_password(service, username)
            except PasswordDeleteError:
                # It's OK: the password was not available in the local keyring
                print("WARNING: {}/{} not found in OS keyring".format(
                    service, username))


def _escape_char(c):
    if isinstance(c, int):
        c = six.unichr(c)
    return c if c in LEGAL_CHARS else ESCAPE_FMT.format(ord(c))


def _escape_for_s3(value):
    return "".join(_escape_char(c) for c in value.encode('utf-8'))
