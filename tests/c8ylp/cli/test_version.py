"""Help tests"""
import re

from click.testing import CliRunner
from c8ylp.main import cli
from tests.env import Environment


def test_show_version(env: Environment):
    """Test show version"""
    runner = CliRunner()
    result = runner.invoke(cli, ["version"], env=env.create_empty_env())
    assert re.match(r"Version \S+\n", result.output) is not None
