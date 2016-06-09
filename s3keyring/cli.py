"""Command line interface"""

from __future__ import print_function

import click
import s3keyring.s3
from s3keyring.settings import config
import os


def _get_default_config_file():
    """Gets the full path to the default config file"""
    project_file = os.path.join(os.path.curdir, '.s3keyring.ini')
    if os.path.isfile(project_file):
        return project_file
    else:
        return os.path.join(os.path.expanduser('~'), '.s3keyring.ini')


@click.group(name='s3keyring')
@click.option("--profile", default='default', metavar='NAME',
              help="The name of configuration profile.")
@click.pass_context
def main(ctx, profile):
    """S3 backend for Python's keyring module."""
    config.boto_config.activate_profile(profile)
    kr = s3keyring.s3.S3Keyring()
    ctx.obj = {'keyring': kr}


@main.command()
@click.option('--ask/--no-ask', default=True)
@click.option("--local/--no-local",
              help="Save configuration in a file under the current directory",
              default=False)
@click.pass_context
def configure(ctx, ask, local):
    """Configure the S3 backend."""
    config.boto_config.configure(ask=ask, local=local)


@main.command()
@click.argument('service')
@click.argument('username')
@click.pass_context
def get(ctx, service, username):
    """Get password for a service/username."""
    click.echo(ctx.obj['keyring'].get_password(service, username))


@main.command()
@click.argument('service')
@click.argument('username')
@click.argument('password')
@click.pass_context
def set(ctx, service, username, password):
    """Set a password for a service/username."""
    click.echo(ctx.obj['keyring'].set_password(service, username, password))


@main.command()
@click.argument('service')
@click.argument('username')
@click.pass_context
def delete(ctx, service, username):
    """Deletes a password for a service/username."""
    click.echo(ctx.obj['keyring'].delete_password(service, username))


if __name__ == '__main__':
    main()
