# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
#     from pytest.mark import parametrize
#
import pytest
from s3keyring import cli
import uuid
from click.testing import CliRunner
from s3keyring.s3 import S3Keyring, configure, supported
from keyring.errors import PasswordDeleteError
parametrize = pytest.mark.parametrize


@pytest.fixture
def keyring(scope='module'):
    configure(ask=False)
    return S3Keyring()


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
def test_help(helparg, capsys, cli_runner):
    result = cli_runner.invoke(cli.main, [helparg])
    assert result.exit_code == 0
    assert 's3keyring' in result.output


class TestCli(object):
    pytestmark = pytest.mark.skipif(
        not supported(), reason="S3 backend has not been configured in this "
                                "system")

    def test_configure_no_ask(self, cli_runner):
        result = cli_runner.invoke(cli.configure, ['--no-ask'])
        assert result.exit_code == 0

    def test_configure_ask(self, cli_runner):
        result = cli_runner.invoke(cli.configure, ['--ask'])
        assert result.exit_code == 1
        assert 'AWS region' in result.output

    def test_set_password(self, cli_runner, random_entry, keyring):
        result = cli_runner.invoke(cli.set, random_entry)
        assert result.exit_code == 0
        pwd = keyring.get_password(*random_entry[:2])
        assert pwd == random_entry[2]

    def test_delete_password(self, cli_runner, random_entry, keyring):
        keyring.set_password(*random_entry)
        assert random_entry[2] == keyring.get_password(*random_entry[:2])
        result = cli_runner.invoke(cli.delete, random_entry[:2])
        assert result.exit_code == 0
        assert keyring.get_password(*random_entry[:2]) is None
