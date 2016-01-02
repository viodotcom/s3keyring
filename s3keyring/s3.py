#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function
import os
import base64
from s3keyring.config import Config
from keyring.errors import (PasswordDeleteError)
from keyring.backend import KeyringBackend
from boto3.session import Session
from botocore.exceptions import EndpointConnectionError
from s3keyring.exceptions import ProfileNotFoundError
import string
import six
import keyring
import sys
import configparser


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


class S3Backed(object):
    def __init__(self, profile=None, profile_name=None):
        """Creates a S3 bucket for the backend if one does not exist already"""
        self.config = Config()

        if profile_name is None:
            # There must be a profile associated to a keyring
            self.profile_name = self.config.get('default', 'profile')
        else:
            self.profile_name = profile_name

        if profile is None:
            # Either the user passes the profile as a dict, or must be read
            # from the config file.
            try:
                self.profile = self.config.get_profile(self.profile_name)
            except ProfileNotFoundError:
                self.config.initialize_profile(self.profile_name)
                self.profile = self.config.get_profile(self.profile_name)
        elif profile_name is None:
            raise InitError("You must provide parameter 'profile_name' when "
                            "providing a 'profile'")
        else:
            self.profile = profile

        self.__s3 = None
        self.__session = None
        # Will store a boto3 Bucket object
        self.__bucket = None

    def supported(self):
        try:
            client = self.session.client('s3')
            resp = client.list_objects(Bucket=self.bucket.name)
            return resp['ResponseMetadata']['HTTPStatusCode'] == 200
        except:
            return False

    @property
    def session(self):
        if self.__session is None:
            aws_profile = self.profile.get('aws_profile')
            if aws_profile == '' or aws_profile == 'default':
                # Use the default creds for this system (maybe temporary
                # creds from a role)
                self.__session = Session()
            else:
                self.__session = Session(
                    profile_name=self.profile.get('aws_profile'))
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

    def configure(self, ask=True, **kwargs):
        """Configures the keyring, requesting user input if necessary"""
        fallback = {'namespace': 'default'}
        for option in ['kms_key_id', 'bucket', 'namespace', 'aws_profile']:
            value = kwargs.get(option) or \
                self.get_config(option, ask=ask, fallback=fallback)
            self.config.set_in_profile(self.profile_name, option, value)

        # We just updated the ini file: reload
        self.profile = self.config.get_profile(self.profile_name)

        self._check_config()
        self._configure_signature()

    def _configure_signature(self):
        """Sets up the AWS profile to use signature version 4"""
        aws_profile = self.config.get_from_profile(self.profile_name,
                                                   'aws_profile')
        awscli_config_dir = os.path.join(os.path.expanduser('~'), '.aws')
        if not os.path.isdir(awscli_config_dir):
            os.makedirs(awscli_config_dir)
        awscli_config_file = os.path.join(awscli_config_dir, 'config')
        cfg = configparser.ConfigParser()
        cfg.read(awscli_config_file)
        if aws_profile is None or aws_profile == 'default':
            section = 'default'
        else:
            section = "profile " + aws_profile

        if section in cfg.sections():
            cfg[section]['s3'] = "\nsignature_version = s3v4"
        else:
            cfg[section] = {'s3': "\nsignature_version = s3v4"}

        with open(awscli_config_file, 'w') as f:
            cfg.write(f)

    def _check_config(self):
        """Checks that the configuration is not obviously wrong"""
        required = ['kms_key_id', 'bucket']
        for option in required:
            val = self.profile.get(option, None)
            if val is None or len(val) == 0:
                print("WARNING: {} is required. You must run s3keyring "
                      "configure again.".format(option),
                      file=sys.stderr)

    def get_config(self, option, ask=True, fallback=None):
        val = self.profile.get(option.lower())
        if val is None or val == '':
            val = os.environ.get("KEYRING_" + option.upper())
        if fallback and val is None:
            val = fallback.get(option.lower())
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
