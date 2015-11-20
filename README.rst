================================
S3 backend for Python's keyring
================================

.. image:: https://circleci.com/gh/InnovativeTravel/s3-keyring.svg?style=svg
    :target: https://circleci.com/gh/InnovativeTravel/s3-keyring

This module adds an `AWS S3`_ backend to Python's keyring_ module. The S3
backend will store the keyring credentials in an S3 bucket and use client and
server side encryption to keep the credentials safe both during transit and at
rest. This backend is quite handy when you want to distribute credentials across
multiple machines. Access to the backend and to the encryption keys can be
finely tuned using AWS IAM policies.

.. _AWS S3: https://aws.amazon.com/s3/
.. _keyring: https://pypi.python.org/pypi/keyring
.. _Key Management System: https://aws.amazon.com/kms/


Installation
------------

You can install a stable release from Pipy::

    pip install s3keyring


Or you can choose to install the development version::

    pip install git+https://github.com/InnovativeTravel/s3-keyring



Prerequisites
------------


S3 bucket
~~~~~~~~~

The S3 keyring backend requires you to have read/write access to a S3 bucket.
If you want to use bucket ``mysecretbucket`` to store your keyring, you will
need to attach the following `IAM policy`_ to your IAM user account or IAM
role::

    {
        "Statement": [
            {
                "Action": [
                    "s3:ListBucket",
                    "s3:PutObject",
                    "s3:GetObject"
                ],
                "Effect": "Allow",
                "Resource": [
                    "arn:aws:s3:::mysecretbucket"
                    "arn:aws:s3:::mysecretbucket/*"
                ]
            }
        ],
        "Version": "2012-10-17"
    }

.. _IAM policy: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-policies-for-amazon-ec2.html


Encryption key
~~~~~~~~~~~~~~

You will also need to create a `KMS encryption key`_. Write down the ID of the
KMS key that you create because you will need it later when you configure
the ``s3keyring`` module.

.. _KMS encryption key: http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html


Configuration
-------------


Quick configuration
~~~~~~~~~~~~~~~~~~~

If you haven't done so already, you will need to configure your local
installation of the AWS SDK by running::

    aws configure


You also need to ensure that you are using version 4 of the AWS Signature for
authenticated requests to S3::

    aws configure set s3.signature_version s3v4


Then you can simply run::

    s3keyring configure


Configuration using profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use ``s3keyring`` to store (read) secrets in (from) more than one 
backend S3 keyring. A typical use case is creating different keyrings for 
different user groups that have different levels of trust. For instance you 
can configure a keyring to store secrets that only administrators can access::

    s3keyring --profile administrators configure


Then you can create an independent keyring to store secrets that need to be 
accessed by EC2 instances associated to the IAM profile ``website-workers``::

    s3keyring --profile website-workers configure

To store and retrieve secrets in the administrators keyring::

    s3keyring --profile administrators set_password service account pwd
    s3keyring --profile administrators get_password service account


And you can obviously do the same for the ``website-workers`` keyring using
option ``--profile website-workers``.


Profile configuration options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A ``s3keyring`` profile consists of the following options:

* ``kms_key_id``: The ID of the `KMS`_ key that will be used to stored secrets
  in the associated keyring. You will need to configure KMS in AWS so that the
  relevant users/groups/profiles have access to this key.

* ``bucket``: The S3 bucket that will hold the keyring. You should associate
  the minimal access IAM policy mentioned at the beginning of this doc to all
  users/groups/roles that will access the keyring.

* ``namespace``: The S3 prefix under which the keyring will be stored.

* ``aws_profile``: The `AWS profile`_ to use when accessing AWS services like 
  KMS and S3. If you intend to use `IAM Roles`_ to grant access to your keyring
  then you should not specify any ``aws_profile`` (or set it to ``default``).


Usage
-----

The ``s3keyring`` module provides the same API as Python's `keyring module`_.
You can access your S3 keyring programmatically from your Python code like
this::


    from s3keyring.s3 import S3Keyring
    kr = S3Keyring()
    kr.set_password('service', 'username', '123456')
    assert '123456' == kr.get_password('service', 'username')
    kr.delete_password('service', 'username')
    assert kr.get_password('service', 'username') is None


You can also use the keyring from the command line::

    # Store a password
    s3keyring set service username 123456
    # Retrieve it
    s3keyring get service username
    # Delete it
    s3keyring delete service username







.. _keyring module: https://pypi.python.org/pypi/keyring


Automatic Deployments
--------------------

You can configure the ``s3keyring`` module without user input by setting
the following environment variables in the deployment target:

* ``AWS_REGION``: The AWS region of the keyring bucket
* ``KEYRING_BUCKET``: The name of the bucket that will hold the keyring data.
* ``KEYRING_NAMESPACE``: The root S3 prefix for the keyring data. If not
  specified, keyring data will be stored under ``s3://$KEYRING_BUCKET/default``
* ``KMS_KEY_ID``: The ID of the KMS key used to encrypt the keyring secrets.

If these environment variables are properly set then you can configure the
``s3keyring`` module automatically using::

    s3keyring configure --no-ask



Who do I ask?
-------------

* German Gomez-Herrero, <german@innovativetravel.eu>
