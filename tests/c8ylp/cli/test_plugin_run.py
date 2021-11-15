"""Plugin run"""

import pytest
import responses
from click.testing import CliRunner
from c8ylp.main import cli
from tests.env import Environment
from tests.fixtures import FixtureCumulocityAPI


def test_plugin_run_command(
    c8yserver: FixtureCumulocityAPI,
    env: Environment,
    capfd: pytest.CaptureFixture,
):
    """Test running custom command after the proxy server starts"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        port = "2223"
        c8yserver.simulate_pre_authenticated(serial)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "plugin",
                serial,
                "--port",
                port,
                "--",
                "/bin/bash",
                "-c",
                "echo 'DEVICE=$DEVICE,PORT=$PORT'; exit 99",
            ],
            env=env.create_authenticated(),
        )

        assert result.exit_code == 99

        # sys stdout is not captured by the CliRunner
        sys_out, _ = capfd.readouterr()
        assert (
            sys_out == f"DEVICE={serial},PORT={port}\n"
        ), "Expect injected env variables"

    run()
