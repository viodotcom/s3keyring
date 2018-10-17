#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Command line interface"""

from __future__ import print_function

import click
import s3keyring.s3
import os


def _get_default_config_file():
    """Gets the full path to the default config file"""
    project_file = os.path.join(os.path.curdir, 's3keyring.ini')
    if os.path.isfile(project_file):
        return project_file
    else:
        return os.path.join(os.path.expanduser('~'), '.s3keyring.ini')


@click.group(name='s3keyring')
@click.option('--profile', default='default')
@click.option('--config', default=_get_default_config_file(),
              metavar='CONFIG_FILE',
              help="The location of the s3keyring configuration file.")
@click.pass_context
def main(ctx, profile, config):
    """S3 backend for Python's keyring module
    """
    kr = s3keyring.s3.S3Keyring(profile_name=profile, config_file=config)
    ctx.obj = {'keyring': kr}


@main.command()
@click.option('--ask/--no-ask', default=True)
@click.pass_context
def configure(ctx, ask):
    """Configure the S3 backend"""
    # If the user specifies an AWS CLI profile, then just read we can from the
    # ~/.aws/credentials and ~/.aws/config files
    ctx.obj['keyring'].configure(ask=ask)


@main.command()
@click.argument('service')
@click.argument('username')
@click.pass_context
def get(ctx, service, username):
    """Gets a password for a service/username"""
    click.echo(ctx.obj['keyring'].get_password(service, username))


@main.command()
@click.argument('service')
@click.argument('username')
@click.argument('password')
@click.pass_context
def set(ctx, service, username, password):
    """Sets a password for a service/username"""
    click.echo(ctx.obj['keyring'].set_password(service, username, password))


@main.command()
@click.argument('service')
@click.argument('username')
@click.pass_context
def delete(ctx, service, username):
    """Deletes a password for a service/username"""
    click.echo(ctx.obj['keyring'].delete_password(service, username))


@main.command()
@click.pass_context
def build_cache(ctx):
    """Builds cache for a namespace"""
    click.echo(ctx.obj['keyring'].build_cache())


@main.command()
@click.pass_context
def get_cache(ctx):
    """Returns cache for a namespace"""
    click.echo(ctx.obj['keyring'].get_cache())


if __name__ == '__main__':
    main()
