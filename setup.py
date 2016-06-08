"""Setuptools entrypoint."""
import codecs
import os

from setuptools import setup

from s3keyring import __version__, __author__

dirname = os.path.dirname(__file__)

long_description = (
    codecs.open(os.path.join(dirname, "README.rst"), encoding="utf-8").read() + "\n" +   # noqa
    codecs.open(os.path.join(dirname, "AUTHORS.rst"), encoding="utf-8").read() + "\n" +  # noqa
    codecs.open(os.path.join(dirname, "CHANGES.rst"), encoding="utf-8").read()
)

setup(
    name="s3keyring",
    include_package_data=True,
    package_data={"s3keyring": ["s3keyring.ini"]},
    packages=["s3keyring"],
    version=__version__,
    license="MIT",
    author=__author__,
    author_email="data@findhotel.net",
    url="http://github.com/findhotel/s3keyring",
    description="S3 backend for Python's keyring module",
    long_description=long_description,
    install_requires=[
        "click>=5.1",
        "keyring",
        "boto3facade>=0.2.4",
        "awscli",
    ],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3"
    ],
    zip_safe=False,
    entry_points={
        "console_scripts": [
            "s3keyring = s3keyring.cli:main",
        ]
    }
)
