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


@main.command()
@click.argument('service')
@click.argument('username')
def get(service, username):
    """Gets a password for a service/username"""
    kr = s3keyring.s3.S3Keyring()
    click.echo(kr.get_password(service, username))


@main.command()
@click.argument('service')
@click.argument('username')
@click.argument('password')
def set(service, username, password):
    """Sets a password for a service/username"""
    kr = s3keyring.s3.S3Keyring()
    click.echo(kr.set_password(service, username, password))


@main.command()
@click.argument('service')
@click.argument('username')
def delete(service, username):
    """Deletes a password for a service/username"""
    kr = s3keyring.s3.S3Keyring()
    click.echo(kr.delete_password(service, username))


if __name__ == '__main__':
    main()
