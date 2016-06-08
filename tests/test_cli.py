"""Test s3keyring CLI."""

import logging

from click.testing import CliRunner

from s3keyring import cli

logging.getLogger().setLevel("ERROR")


class TestCli(object):
    def test_configure_existing_profile_no_ask(self, keyring):
        """Re-configure a profile that we know already exists."""
        result = CliRunner().invoke(cli.main, ["--profile", "test",
                                               "configure", "--no-ask"])
        assert result.exit_code == 0

    def test_help(self):
        result = CliRunner().invoke(cli.main, ["--help"])
        assert result.exit_code == 0 and "s3keyring" in result.output

    def test_set_password(self, random_entry, keyring):
        result = CliRunner().invoke(cli.main, ['--profile', 'test', 'set'] +
                                    list(random_entry))
        assert result.exit_code == 0
        pwd = keyring.get_password(*random_entry[:2])
        assert pwd == random_entry[2]
        keyring.delete_password(*random_entry[:2])
        assert keyring.get_password(*random_entry[:2]) is None

    def test_delete_password(self, random_entry, keyring):
        keyring.set_password(*random_entry)
        assert random_entry[2] == keyring.get_password(*random_entry[:2])
        result = CliRunner().invoke(cli.main, ['--profile', 'test', 'delete'] +
                                    list(random_entry)[:2])
        assert result.exit_code == 0
        assert keyring.get_password(*random_entry[:2]) is None
