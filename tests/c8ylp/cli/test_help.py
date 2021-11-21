"""Help tests"""
import re
import subprocess
import sys
from click.testing import CliRunner
from c8ylp.main import cli


def test_calling_root_module():
    """Test calling root module using python3 -m syntax"""

    # pylint: disable=subprocess-run-check
    proc = subprocess.run(
        [sys.executable, "-m", "c8ylp"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0

    output = proc.stdout.decode()
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
