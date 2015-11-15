#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import base64
import boto3
import s3keyring
from keyring.errors import (PasswordDeleteError)
from keyring.backend import KeyringBackend
from boto3.session import Session
from botocore.exceptions import EndpointConnectionError
from s3keyring import ProfileNotFoundError
import string
import six
import keyring
import sys


LEGAL_CHARS = (
    getattr(string, 'letters', None)     # Python 2.x
    or getattr(string, 'ascii_letters')  # Python 3.x
    ) + string.digits + '/_-'

ESCAPE_FMT = "_{}02X"


class PasswordGetError(Exception):
    """Raised when there is an error retrieving a password.
    """
    pass


class InitError(Exception):
    """Raised when the S3 backend has not been properly initialized
    """
    pass


def supported():
    """Returns True if the S3 backed is supported on this system"""
    try:
        kr = S3Keyring()
        kr.configure(ask=False)
        profile = s3keyring.read_config('default', 'profile')
        profile = s3keyring.read_profile(profile)
        aws_profile = profile.get('aws_profile', profile)
        session = boto3.session.Session(profile_name=aws_profile)
        bucket = profile.get('bucket')
        if not bucket:
            return False
        client = session.client('s3')
        resp = client.list_objects(Bucket=bucket)
        return resp['ResponseMetadata']['HTTPStatusCode'] == 200
    except:
        return False


class S3Backed(object):
    def __init__(self, profile=None, profile_name=None):
        """Creates a S3 bucket for the backend if one does not exist already"""
        if profile_name is None:
            # There must be a profile associated to a keyring
            self.profile_name = s3keyring.read_config('default', 'profile')
        else:
            self.profile_name = profile_name

        if profile is None:
            # Either the user passes the profile as a dict, or must be read
            # from the config file.
            try:
                self.profile = s3keyring.read_profile(self.profile_name)
            except ProfileNotFoundError:
                s3keyring.initialize_profile_config(self.profile_name)
                self.profile = s3keyring.read_profile(self.profile_name)
        elif profile_name is None:
            raise InitError("You must provide parameter 'profile_name' when "
                            "providing a 'profile'")
        else:
            self.profile = profile

        self.__s3 = None
        self.__session = None
        # Will store a boto3 Bucket object
        self.__bucket = None

    @property
    def session(self):
        if self.__session is None:
            self.__session = Session(profile_name=self.profile['aws_profile'])
        return self.__session

    @property
    def kms_key_id(self):
        return self.profile['kms_key_id']

    @property
    def bucket(self):
        if self.__bucket is None:
            bucket_name = self.profile['bucket']
            self.__bucket = self.session.resource('s3').Bucket(bucket_name)
        return self.__bucket

    @property
    def use_local_keyring(self):
        return self.profile.get('use_local_keyring', 'no') == 'yes'

    @property
    def region(self):
        return self.profile['region']

    @property
    def s3(self):
        if self.__s3 is None:
            self.__s3 = self.session.resource('s3')
        return self.__s3

    @property
    def namespace(self):
        """Namespaces allow you to have multiple keyrings backed by the same
        S3 bucket by separating them with different S3 prefixes. Different
        access permissions can then be given to different prefixes so that
        only the right IAM roles/users/groups have access to a keychain
        namespace"""
        return _escape_for_s3(self.profile['namespace'])

    def configure(self, ask=True):
        """Configures the keyring, requesting user input if necessary"""
        region = self._get_region(ask=ask)
        s3keyring.write_profile_config(self.profile_name, 'region', region)

        fallback = {'namespace': 'default', 'aws_profile': self.profile_name}
        for option in ['kms_key_id', 'bucket', 'namespace', 'aws_profile']:
            value = self.get_config(option, ask=ask, fallback=fallback)
            s3keyring.write_profile_config(self.profile_name, option, value)

        # We just updated the ini file: so reload the profile info
        self.profile = s3keyring.read_profile(self.profile_name)

        # Make sure the profile configuration is correct
        self._check_config()

    def _get_region(self, ask=True):
        """Gets the profile region, maybe requesting user input"""
        region = self.profile.get('region', '')
        if region == '':
            region = os.environ.get('KEYRING_REGION', '')
        if ask:
            resp = input("AWS region [{}]: ".format(region))
            if len(resp) > 0:
                return resp
        return region

    def _check_config(self):
        """Checks that the configuration is not obviously wrong"""
        required = ['kms_key_id', 'region', 'bucket']
        for option in required:
            val = self.profile.get(option, None)
            if val is None or len(val) == 0:
                print("WARNING: {} is required. You must run s3keyring "
                      "configure again.".format(option),
                      file=sys.stderr)

    def get_config(self, option, ask=True, fallback=None):
        val = self.profile.get(option.lower(), '')
        if val is None or val == '':
            val = os.environ.get("KEYRING_" + option.upper(), '')
        if fallback and val == '':
            val = fallback.get(option.lower(), '')
        if ask:
            resp = input("{} [{}]: ".format(
                option.replace('_', ' ').title(), val))
            if len(resp) > 0:
                return resp
        return val


class S3Keyring(S3Backed, KeyringBackend):
    """
    BaseS3Keyring is a S3-based implementation of keyring.
    This keyring stores the password directly in S3 and provides methods
    which may be overridden by subclasses to support
    encryption and decryption. The encrypted payload is stored in base64
    format.
    """

    def _get_s3_key(self, service, username):
        """The S3 key where the secret will be stored"""
        return "{}/{}/{}/secret.b64".format(self.namespace, service, username)

    def get_value(self, *args, **kwargs):
        """An alias of method get_password"""
        return self.get_password(*args, **kwargs)

    def get_password(self, service, username):
        """Read the password from the S3 bucket.
        """
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
        pwd = base64.decodestring(pwd_base64)
        return pwd.decode('utf-8')

    def set_value(self, *args, **kwargs):
        """An alias for method set_password"""
        return self.set_password(*args, **kwargs)

    def set_password(self, service, username, password):
        """Write the password in the S3 bucket.
        """
        service = _escape_for_s3(service)
        username = _escape_for_s3(username)

        pwd_base64 = base64.encodestring(password.encode('utf-8')).decode()

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
            else:
                raise

        # We also save the password in the local OS keyring. This will allow us
        # to retrieve the password locally if the S3 bucket would not be
        # available.
        keyring.set_password(service, username, password)

    def delete_value(self, *args, **kwargs):
        """An alias for delete_password"""
        return self.delete_password(*args, **kwargs)

    def delete_password(self, service, username):
        """Delete the password for the username of the service.
        """
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
