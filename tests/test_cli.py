# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
#     from pytest.mark import parametrize
#
import pytest
from s3keyring import cli
import uuid
from click.testing import CliRunner
from s3keyring.s3 import S3Keyring, supported
from keyring.errors import PasswordDeleteError
parametrize = pytest.mark.parametrize


@pytest.fixture
def keyring(scope='module'):
    kr = S3Keyring()
    kr.configure(ask=False)
    return kr


@pytest.fixture
def cli_runner(scope='module'):
    return CliRunner()


@pytest.yield_fixture
def random_entry(keyring, scope='function'):
    service = str(uuid.uuid4())
    user = str(uuid.uuid4())
    pwd = str(uuid.uuid4())
    yield (service, user, pwd)
    # Cleanup
    try:
        keyring.delete_password(service, user)
    except PasswordDeleteError as err:
        if 'not found' not in err.args[0]:
            # It's ok if the entry has been already deleted
            raise


@parametrize('helparg', ['--help'])
def test_help(helparg, cli_runner):
    result = cli_runner.invoke(cli.main, [helparg])
    assert result.exit_code == 0
    assert 's3keyring' in result.output


class TestCli(object):
    pytestmark = pytest.mark.skipif(
        not supported(), reason="S3 backend not supported or not configured")

    def test_configure_no_ask(self, cli_runner):
        result = cli_runner.invoke(cli.main, ['configure', '--no-ask'])
        # Assumes the envvars have been set as described in README
        assert result.exit_code == 0

    def test_configure_profile(self, cli_runner):
        result = cli_runner.invoke(cli.main, ['--profile', 'dummy',
                                              'configure', '--no-ask'])
        # Assumes the envvars have been set as described in README
        assert result.exit_code == 0

    def test_configure_ask(self, cli_runner):
        result = cli_runner.invoke(cli.main, ['configure', '--ask'])
        assert result.exit_code == 1
        assert 'Kms Key Id' in result.output

    def test_set_password(self, cli_runner, random_entry, keyring):
        result = cli_runner.invoke(cli.main, ['set'] + list(random_entry))
        assert result.exit_code == 0
        pwd = keyring.get_password(*random_entry[:2])
        assert pwd == random_entry[2]

    def test_delete_password(self, cli_runner, random_entry, keyring):
        keyring.set_password(*random_entry)
        assert random_entry[2] == keyring.get_password(*random_entry[:2])
        result = cli_runner.invoke(cli.main, ['delete'] +
                                   list(random_entry)[:2])
        assert result.exit_code == 0
        assert keyring.get_password(*random_entry[:2]) is None
