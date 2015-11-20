#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command line interface"""

from __future__ import print_function

import click
import s3keyring.s3


def setup_keyring(profile_name):
    return s3keyring.s3.S3Keyring(profile_name=profile_name)


@click.group(name='s3keyring')
@click.option('--profile', default='default')
@click.pass_context
def main(ctx, profile):
    """S3 backend for Python's keyring module
    """
    ctx.obj = {'profile': profile}


@main.command()
@click.option('--ask/--no-ask', default=True)
@click.pass_context
def configure(ctx, ask):
    """Configure the S3 backend"""
    # If the user specifies an AWS CLI profile, then just read we can from the
    # ~/.aws/credentials and ~/.aws/config files
    setup_keyring(ctx.obj['profile']).configure(ask=ask)


@main.command()
@click.argument('service')
@click.argument('username')
@click.pass_context
def get(ctx, service, username):
    """Gets a password for a service/username"""
    click.echo(setup_keyring(ctx.obj['profile']).get_password(
        service, username))


@main.command()
@click.argument('service')
@click.argument('username')
@click.argument('password')
@click.pass_context
def set(ctx, service, username, password):
    """Sets a password for a service/username"""
    click.echo(setup_keyring(ctx.obj['profile']).set_password(
        service, username, password))


@main.command()
@click.argument('service')
@click.argument('username')
@click.pass_context
def delete(ctx, service, username):
    """Deletes a password for a service/username"""
    click.echo(setup_keyring(ctx.obj['profile']).delete_password(
        service, username))


if __name__ == '__main__':
    main()
