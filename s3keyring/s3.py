#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import base64
import boto3
import uuid
import s3keyring
from configparser import NoOptionError, NoSectionError
from keyring.errors import (PasswordDeleteError, InitError)
from keyring.backend import KeyringBackend
from boto3.session import Session
from botocore.exceptions import EndpointConnectionError
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


class ConfigError(Exception):
    """Raised when the S3 backend has not been properly configured
    """


def supported():
    """Returns True if the S3 backed is supported on this system"""
    try:
        bucket = _get_config('aws', 'keyring_bucket')
        resp = boto3.client('s3').list_objects(Bucket=bucket)
        return resp['ResponseMetadata']['HTTPStatusCode'] == 200
    except:
        return False


class S3Backed(object):
    def __init__(self, kms_key_id=None, region=None, profile=None):
        """Creates a S3 bucket for the backend if one does not exist already"""
        self.__s3 = None
        self.__bucket = None
        self.__namespace = None
        self.__region = region
        self.__profile = profile
        self.__kms_key_id = kms_key_id
        self.__session = None

    @property
    def session(self):
        if self.__session is None:
            self.__session = Session(region_name=self.region)
        return self.__session

    @property
    def kms_key_id(self):
        if self.__kms_key_id is None:
            self.__kms_key_id = _get_config('aws', 'kms_key_id')
        return self.__kms_key_id

    @property
    def bucket(self):
        if self.__bucket is None:
            name = _get_config('aws', 'keyring_bucket', throw=False)
            if name is None:
                self.__bucket = self._find_bucket(name)
            else:
                self.__bucket = boto3.resource('s3').Bucket(name)
        return self.__bucket

    @property
    def region(self):
        if self.__region is None:
            self.__region = s3keyring.read_config('aws', 'region')
        return self.__region

    @property
    def profile(self):
        if self.__profile is None:
            self.__profile = _get_config('aws', 'profile')
        return self.__profile

    @property
    def name(self):
        return self.bucket.name.split('keyring-')[1]

    @property
    def s3(self):
        if self.__s3 is None:
            self.__s3 = boto3.resource('s3')
        return self.__s3

    @property
    def namespace(self):
        """Namespaces allow you to have multiple keyrings backed by the same
        S3 bucket by separating them with different S3 prefixes. Different
        access permissions can then be given to different prefixes so that
        only the right IAM roles/users/groups have access to a keychain
        namespace"""
        if self.__namespace is None:
            self.__namespace = _escape_for_s3(_get_config('aws',
                                                          'keyring_namespace'))

        return self.__namespace

    def _find_bucket(self):
        """Finds the backend S3 bucket. The backend bucket must be called
        keyring-[UUID].
        """
        bucket = [b for b in self.s3.buckets.all()
                  if b.name.find('keyring-') == 0]
        if len(bucket) == 0:
            bucket_name = "keyring-{}".format(uuid.uuid4())
            bucket = self.s3.Bucket(bucket_name)
            bucket.create(ACL='private',
                          CreateBucketConfiguration={
                              'LocationConstraint': self.region})
        elif len(bucket) > 1:
            msg = ("Can't tell which of these buckets to use for the keyring: "
                   "{buckets}").format([b.name for b in bucket])
            raise InitError(msg)
        else:
            bucket = bucket[0]
        return bucket

    def _get_profile_default(self, profile, option):
        """Gets a default option value for a given AWS profile"""
        if profile not in self.config:
            profile = 'default'

        if option not in self.config[profile]:
            raise ConfigError("No default for option {} in profile {}".format(
                option, profile))

        return self.config[profile][option]


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
            # Can't connect to S3: fallback to the local keyring
            print("WARNING: can't connect to S3, falling back to OS keyring",
                  file=sys.stderr)
            return keyring.get_password(service, username)

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
            # Can't connect to S3: fallback to OS keyring
            print("WARNING: can't connect to S3, storing in OS keyring",
                  file=sys.stderr)
            keyring.set_password(service, username, password)
            return

        # We also save the password in the local OS keyring. This will allow us
        # to retrieve the password locally if the S3 bucket would not be
        # available.
        keyring.set_password(service, username, password)

    def delete_password(self, service, username):
        """Delete the password for the username of the service.
        """
        service = _escape_for_s3(service)
        username = _escape_for_s3(username)
        prefix = self._get_s3_key(service, username)
        objects = list(self.bucket.objects.filter(Prefix=prefix))
        if len(objects) == 0:
            msg = ("Password for service {service} and username {username} "
                   "not found.").format(service=service, username=username)
            raise PasswordDeleteError(msg)
        elif len(objects) > 1:
            msg = ("Multiple objects in bucket {bucket} match the prefix "
                   "{prefix}.").format(bucket=self.bucket.name,
                                       prefix=prefix)
        else:
            objects[0].delete()

        # Delete also in the local keyring
        try:
            keyring.delete_password(service, username)
        except PasswordDeleteError:
            # It's OK: the password was not available in the local keyring
            pass


def _escape_char(c):
    if isinstance(c, int):
        c = six.unichr(c)
    return c if c in LEGAL_CHARS else ESCAPE_FMT.format(ord(c))


def _escape_for_s3(value):
    return "".join(_escape_char(c) for c in value.encode('utf-8'))


def _get_config(section, option, throw=True):
    """Gets a configuration option or throws exception if not configured"""
    try:
        return s3keyring.read_config(section, option)
    except (NoOptionError, NoSectionError):
        if throw:
            raise InitError("You need to run: s3keyring configure")


def configure(ask=True):
    """Configures the keyring, requesting user input if necessary"""
    region = _get_region(ask=ask)
    s3keyring.write_config('aws', 'region', region)

    fallback = {'keyring_namespace': 'default'}
    for option in ['kms_key_id', 'keyring_bucket', 'keyring_namespace']:
        value = _get_keyring_config(option, ask=ask, fallback=fallback)
        s3keyring.write_config('aws', option, value)

    # Make sure the configuration was correct
    check_config()


def check_config():
    """Checks that the configuration is not obviously wrong"""
    required = ['kms_key_id', 'region', 'keyring_bucket']
    for option in required:
        val = _get_config('aws', option, throw=False)
        if val is None or len(val) == 0:
            print("WARNING: {} is required. You must run s3keyring "
                  "configure again.".format(option),
                  file=sys.stderr)


def _get_keyring_config(option, ask=True, fallback=None):
    val = s3keyring.read_config('aws', option.lower())
    if val == '':
        val = os.environ.get(option.upper(), '')
    if fallback and val == '':
        val = fallback.get(option.lower(), '')

    if ask:
        resp = input("{} [{}]: ".format(
            option.replace('_', ' ').title(), val))
        if len(resp) > 0:
            return resp

    return val


def _get_region(profile=None, ask=True):
    region = s3keyring.read_config('aws', 'region')

    if region == '':
        region = os.environ.get('AWS_REGION', '')

    if ask:
        resp = input("AWS region [{}]: ".format(region))
        if len(resp) > 0:
            return resp

    return region
