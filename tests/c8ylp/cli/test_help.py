"""Help tests"""
import subprocess
import re
import pytest
from click.testing import CliRunner
from c8ylp.main import cli


def test_calling_root_module(capfd: pytest.CaptureFixture):
    """Test calling root module using python3 -m syntax"""

    with subprocess.Popen(
        ["python", "-m", "c8ylp"],
        env={},
    ) as proc:
        exit_code = proc.wait()
    assert exit_code == 0

    output, _stderr = capfd.readouterr()
    assert re.search("Usage: python3? -m c8ylp ", output)
    assert "Options:" in output


def test_help_without_credentials():
    """Test calling help without any required arguments
    i.e. c8ylp --help
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert "Usage: cli" in result.output
    assert "Options:" in result.output
