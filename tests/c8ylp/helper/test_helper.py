"""Helper cli tests"""

from click.testing import CliRunner
from c8ylp.helper import cli, socketcontext, get_unused_port


def test_port():
    """Test get unused port number"""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["port"],
    )
    assert result.exit_code == 0
    assert 0 <= int(result.output) <= 65535


def test_wait():
    """Test wait for port"""

    with socketcontext() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["wait", str(port), "5"],
        )
        assert result.exit_code == 0


def test_wait_timout_error():
    """Test timeout error whilst waiting for a port"""

    runner = CliRunner()
    port = get_unused_port()
    result = runner.invoke(
        cli,
        ["wait", str(port), "0.5"],
    )
    assert result.exit_code == 1
    assert "Port is not open after 0.5s" in result.output


def test_wait_silent_error():
    """Test wait timeout error but skip stdout message and only set exit code"""

    runner = CliRunner()
    port = get_unused_port()
    result = runner.invoke(
        cli,
        ["wait", str(port), "0.5", "--silent"],
    )
    assert result.exit_code == 1
    assert "Port is not open after" not in result.output
