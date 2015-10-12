# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
#     from pytest.mark import parametrize
#
import pytest
import s3keyring.cli
from click.testing import CliRunner
parametrize = pytest.mark.parametrize


class TestCli(object):
    @parametrize('helparg', ['--help'])
    def test_help(self, helparg, capsys):
        runner = CliRunner()
        result = runner.invoke(s3keyring.cli.main, [helparg])
        assert result.exit_code == 0
        assert 's3keyring' in result.output
