#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command line interface"""

from __future__ import print_function

import click
import s3keyring.s3


@click.group(name='s3keyring')
def main():
    """S3 backend for Python's keyring module
    """
    pass


@main.command()
@click.option('--ask/--no-ask', default=True)
def configure(ask):
    """Configure the S3 backend"""
    # If the user specifies an AWS CLI profile, then just read we can from the
    # ~/.aws/credentials and ~/.aws/config files
    s3keyring.s3.configure(ask=ask)


if __name__ == '__main__':
    main()
