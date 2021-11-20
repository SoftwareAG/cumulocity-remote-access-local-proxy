"""Server tests"""

from unittest.mock import patch

from click.testing import CliRunner
from c8ylp.main import cli


@patch("c8ylp.cli.server.ProxyContext", autospec=True)
def test_server_mode(mock_context):
    """Start a mocked server"""
    mock_context.start.return_value = 0

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["server", "ext-device-01"],
    )
    assert result.exit_code == 0
