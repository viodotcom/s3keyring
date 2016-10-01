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
@click.argument("group")
@click.argument("key")
@click.pass_context
def get(ctx, group, key):
    """Get a secret."""
    click.echo(ctx.obj["keyring"].get_password(group, key))


@main.command()
@click.argument("group")
@click.argument("key")
@click.argument("secret")
@click.pass_context
def set(ctx, group, key, secret):
    """Set a secret."""
    click.echo(ctx.obj["keyring"].set_password(group, key, secret))


@main.command(name="list-keys")
@click.argument("group")
@click.pass_context
def list_keys(ctx, group):
    """List the secret keys in a secrets group."""
    click.echo(ctx.obj["keyring"].list_keys(group))


@main.command()
@click.argument("group")
@click.argument("key")
@click.pass_context
def delete(ctx, group, key):
    """Delete a secret."""
    click.echo(ctx.obj["keyring"].delete_password(group, key))


if __name__ == "__main__":
    main()
