=========================
S3 backend for Python's keyring
=========================

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

Run in a terminal::

    pip install git+https://github.com/InnovativeTravel/s3-keyring


Prerequisites
------------


S3 bucket
~~~~~~~~~

The S3 keyring backend requires you to have read/write access to a S3 bucket.
If you want to use bucket `mysecretbucket` to store your keyring, you will need
to attach the following `IAM policy`_ to your AWS user account::

    {
        "Statement": [
            {
                "Resource": [
                    "arn:aws:s3:::mysecretbucket"
                ],
                "Action": [
                    "s3:*"
                ],
                "Effect": "Allow"
            }
        ],
        "Version": "2012-10-17"
    }


Encryption key
~~~~~~~~~~~~~~

You will also need to create a `KMS encryption key`_. Write down the ID of the
KMS key that you create because you will need it later when you configure
the `s3keyring` module.

.. _KMS encryption key: http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html


Configuration
-------------

If you haven't done so already, you will need to configure your local
installation of the AWS SDK by running::

    aws configure


Then you can simply run::

    s3keyring configure



Who do I ask?
-------------

* German Gomez-Herrero, <german@innovativetravel.eu>
