S3 backend for Python's keyring
================================

.. image:: https://travis-ci.org/FindHotel/s3keyring.svg?branch=master
    :target: https://travis-ci.org/FindHotel/s3keyring

.. |PyPI| image:: https://img.shields.io/pypi/v/s3keyring.svg?style=flat
   :target: https://pypi.python.org/pypi/s3keyring

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

You can install a stable release from Pypi::

    pip install s3keyring


Or you can choose to install the development version::

    pip install git+https://github.com/InnovativeTravel/s3-keyring


In Mac OS X El Capitan and later you may run into permission issues
when running `pip install`. A workaround is to install `s3keyring` using::

    sudo -H pip install --ignore-installed git+https://github.com/InnovativeTravel/s3-keyring

A better solution is to install Python with homebrew so that `pip install` will
not attempt to install packages in any system directory::

    brew install python




For Admins: setting up the keyring
------------------------------------------------

If you are just a user of the keyring and someone else has set up the keyring
for you then you can skip this section and go directly to ``For Keyring Users:
accessing the keyring`` at the end of this README. Note that you will need 
administrator privileges in your AWS account to be able to set up a new keyring 
as described below.




S3 bucket
~~~~~~~~~

The S3 keyring backend requires you to have read/write access to a S3 bucket.
If you want to use bucket ``mysecretbucket`` to store your keyring, you will
need to attach the following `IAM policy`_ to all the IAM user accounts or
roles that will have read and write access to the keyring::

    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket"
                ],
                "Resource": "arn:aws:s3:::mysecretbucket",
                "Condition": {}
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:DeleteObject",
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": "arn:aws:s3:::mysecretbucket/*"
            }
        ]
    }

.. _IAM policy: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-policies-for-amazon-ec2.html

If you want to create a policy that grants read-only access to the keyring then
remove the ``s3:PutObject`` and ``s3:DeleteObject`` actions from the policy
above.




Encryption key
~~~~~~~~~~~~~~

You need to create a `KMS encryption key`_. Write down the ID of the
KMS key that you create. You will need to share this KMS Key ID with the
users of the keyring.

.. _KMS encryption key: http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html


**IMPORTANT**: You will need to grant read access to the KMS key to every IAM
user or role that needs to access the keyring.




For users: accessing the keyring
---------------------------------------------


One-time configuration
~~~~~~~~~~~~~~~~~~~~~~

If you haven't done so already, you will need to configure your local
installation of the `AWS CLI`_ by running::

    aws configure

.. _AWS CLI: http://docs.aws.amazon.com/cli

Then configure the S3 Keyring::

    s3keyring configure

Your keyring administrator will provide you with the ``KMS Key ID``,
``Bucket`` and ``Namespace`` configuration options. Option ``AWS profile``
allows you to specify the local `AWS CLI profile`_ you want to use to sign all
requests sent to AWS when accessing the keyring. Most users will want to use
the ``default`` profile.

.. _AWS CLI profile: http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html#cli-multiple-profiles

**IMPORTANT**: when deploying the `s3keyring` in EC2 instances that are granted
access to the keyring by means of an `IAM role` you should not specify a
custom AWS profile when configuring s3keyring in the instances.

.. _IAM role: http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html


You can configure the ``s3keyring`` module without user input by setting the
following environment variables: ``S3KEYRING_BUCKET``, ``S3KEYRING_NAMESPACE``,
``S3KEYRING_KMS_KEY_ID``, ``S3KEYRING_AWS_PROFILE``. If these environment variables
are properly set then you can configure the ``s3keyring`` module with::

    s3keyring configure --no-ask



Configuration profiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can use ``s3keyring`` to store (read) secrets in (from) more than one
backend S3 keyring. A typical use case is creating different keyrings for 
different user groups that have different levels of trust. For instance your 
keyring administrator may have setup a S3 keyring that only IAM users with admin
privileges can access. Using the bucket, KMS Key ID and namespace provided by 
your keyring admin you can configure a separate ``s3keyring`` profile to access
that admins-only keyring::

    s3keyring --profile administrators configure

Your keyring admin may have also setup a separate S3 keyring to store secrets 
that need to be accessed by EC2 instances that act as backend workers in a
project you are part of. To access that keyring you would configure a
second ``s3keyring`` profile::

    s3keyring --profile website-workers configure

Then, to store and retrieve secrets in the administrators keyring::

    s3keyring --profile administrators set SERVICE ACCOUNT PASSWORD 
    s3keyring --profile administrators get SERVICE ACCOUNT


And you could do the same for the ``website-workers`` keyring using option
``--profile website-workers``.



Configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~

By default ``s3keyring`` reads configuration options from ``~/.s3keyring.ini``.
You can also store the configuration in a ``.s3keyring.ini`` file stored in your
current working directory by using::

    s3keyring configure --local


``s3keyring`` will always read the configuration first from a ``.s3keyring.ini``
file under your current work directory. If it is not found then it will read it
from ``~/.s3keyring.ini``.




Usage
-----

The ``s3keyring`` module provides the same API as Python's `keyring module`_.
You can access your S3 keyring programmatically from your Python code like
this::

    from s3keyring.s3 import S3Keyring
    kr = S3Keyring()
    kr.set_password('groupname', 'username', '123456')
    assert '123456' == kr.get_password('groupname', 'username')
    kr.delete_password('groupname', 'username')
    assert kr.get_password('groupname', 'username') is None


You can also use the keyring from the command line::

    # Store a password
    s3keyring set groupname username 123456
    # Retrieve it
    s3keyring get groupname username
    # Delete it
    s3keyring delete groupname username


.. _keyring module: https://pypi.python.org/pypi/keyring



Recommended workflow
~~~~~~~~~~~~~~~~~~~~

This is how I use ``s3keyring`` in my Python projects.

Let's assume that my project root directory looks something like this::

   setup.py
   my_module/
             __init__.py


In my project root directory I run::

    s3keyring configure --local

I keep the generated ``.s3keyring.ini`` file as part of my project source code
(i.e. under version control). Then in my project code I use the keyring like 
this::

    from s3keyring.s3 import S3Keyring

    keyring = S3Keyring(config_file="/path/to/s3keyring.ini")
    keyring.set_password('service', 'username', '123456')
    assert keyring.get_password('service', 'username') == '123456'


Contact
-------

If you have questions, bug reports, suggestions, etc. please create an issue on
the `GitHub project page <http://github.com/findhotel/s3keyring>`_.



License
-------

This software is licensed under the `MIT license <http://en.wikipedia.org/wiki/MIT_License>`_

See `License file <https://github.com/findhotel/s3keyring/blob/master/LICENSE>`_


© 2020 German Gomez-Herrero, and `FindHotel`_.

.. _FindHotel: https://company.findhotel.net/
