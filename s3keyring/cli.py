"""Command line interface"""

from __future__ import print_function

import click
import s3keyring.s3
from s3keyring.settings import config


@click.group(name="s3keyring")
@click.option("--profile", default='default', metavar="NAME",
              help="The name of configuration profile.")
@click.option("--ini", default=None, metavar="INIFILE",
              help="Path to the keyring configuration file.")
@click.pass_context
def main(ctx, profile, ini):
    """S3 backend for Python's keyring module."""
    config.boto_config.activate_profile(profile)
    kr = s3keyring.s3.S3Keyring(config_file=ini)
    ctx.obj = {"keyring": kr}


@main.command()
@click.option("--ask/--no-ask", default=True)
@click.option("--local/--no-local",
              help="Save configuration in a file under the current directory",
              default=False)
@click.pass_context
def configure(ctx, ask, local):
    """Configure the S3 backend."""
    config.boto_config.configure(ask=ask, local=local)


@main.command()
@click.argument("service")
@click.argument("key")
@click.pass_context
def get(ctx, service, key):
    """Get a secret."""
    click.echo(ctx.obj["keyring"].get_password(service, key))


@main.command()
@click.argument("service")
@click.argument("key")
@click.argument("secret")
@click.pass_context
def set(ctx, service, key, secret):
    """Set a secret."""
    click.echo(ctx.obj["keyring"].set_password(service, key, secret))


@main.command(name="list-keys")
@click.argument("service")
@click.pass_context
def list_keys(ctx, service):
    """List the keys associated to a given service."""
    click.echo(ctx.obj["keyring"].list_keys(service))


@main.command()
@click.argument("service")
@click.argument("key")
@click.pass_context
def delete(ctx, service, key):
    """Delete a secret."""
    click.echo(ctx.obj["keyring"].delete_password(service, key))


if __name__ == "__main__":
    main()
