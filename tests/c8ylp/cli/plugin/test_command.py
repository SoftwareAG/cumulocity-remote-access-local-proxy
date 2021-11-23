"""Plugin run"""

import os
import platform
import shutil
import subprocess
from unittest.mock import patch

import pytest
import responses
from click.testing import CliRunner
from c8ylp.main import cli
from c8ylp.cli.core import ExitCodes
from tests.env import Environment
from tests.fixtures import FixtureCumulocityAPI


@pytest.mark.parametrize(
    "case",
    (
        {
            "commands": ["--", 'echo "DEVICE=$DEVICE,PORT=$PORT"; exit 101'],
            "exit_code": 101,
            "stdout": "DEVICE=ext-device-01,PORT=2223",
        },
        {
            "commands": ['echo "DEVICE=$DEVICE,PORT=$PORT"; exit 101'],
            "exit_code": 101,
            "stdout": "DEVICE=ext-device-01,PORT=2223",
        },
        {
            "commands": [
                "--",
                "bash",
                "-c",
                'echo "DEVICE=$DEVICE,PORT=$PORT"; exit 99',
            ],
            "exit_code": 99,
            "stdout": "DEVICE=ext-device-01,PORT=2223",
        },
        {
            "commands": [
                "--",
                "/bin/doesnotexist",
            ],
            "exit_code": 127,  # Command not found
            "stdout": "non-zero exit code",
        },
        {
            "commands": [],
            "exit_code": 2,  # Unknown properties error (from click)
            "stdout": "At least one argument needs to be provided",
        },
    ),
)
def test_plugin_run_command(
    case,
    c8yserver: FixtureCumulocityAPI,
    env: Environment,
    # capfd: pytest.CaptureFixture,
):
    """Test running custom command after the proxy server starts"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        port = "2223"
        c8yserver.simulate_pre_authenticated(serial)

        # HACK: Prefix the preferred github actions runner
        # path where bash.exe is located so it picks up this version
        # rather than WSL as WSL is not configured in the CI environment
        # Otherwise the bash does not run properly.
        env_path_override = {}
        if platform.system() == "Windows":
            print(f"which bash (before): {shutil.which('bash')}")
            os.environ["PATH"] = (
                "C:\\Program Files\\Git\\bin" + ";" + os.getenv("PATH", "")
            )
            print(f"which bash (after): {shutil.which('bash')}")
            env_path_override["PATH"] = os.environ["PATH"]

        # pylint: disable=subprocess-run-check
        result = subprocess.run(
            [
                "plugin",
                "command",
                "--port",
                port,
                serial,
                *case["commands"],
            ],
            env={
                **os.environ,
                **env.create_authenticated(),
                **env_path_override,
            },
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        sys_out = result.stdout.decode()
        sys_err = result.stderr.decode()

        # Support debugging on CI runner
        print("---DEBUG---: system.output: ", sys_out)
        print("---DEBUG---: system.error: ", sys_err)

        assert result.returncode == case["exit_code"]

        if case["stdout"] is not None:
            assert case["stdout"] in sys_out

        # runner = CliRunner()
        # result = runner.invoke(
        #     cli,
        #     [
        #         "plugin",
        #         "command",
        #         "--port",
        #         port,
        #         serial,
        #         *case["commands"],
        #     ],
        #     env={
        #         **os.environ,
        #         **env.create_authenticated(),
        #         **env_path_override,
        #     },
        # )

        # assert result.exit_code == case["exit_code"]

        # # sys stdout is not captured by the CliRunner
        # sys_out, _ = capfd.readouterr()

        # # Support debugging on CI runner
        # print("---DEBUG---: cli.output: %s", result.output)
        # print("---DEBUG---: system.output: %s", sys_out)

        # if case["stdout"] is not None:
        #     if sys_out:
        #         assert case["stdout"] in sys_out
        #     else:
        #         assert case["stdout"] in result.output

    run()


@patch("shutil.which", return_value=None)
def test_command_with_bash_missing(
    _mock_which,
    c8yserver: FixtureCumulocityAPI,
    env: Environment,
):
    """Test handling when /bin/bash does not exist"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        port = "2223"
        c8yserver.simulate_pre_authenticated(serial)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["plugin", "command", "--port", port, serial, "echo", "dummy output"],
            env=env.create_authenticated(),
        )

        assert result.exit_code == ExitCodes.COMMAND_NOT_FOUND

        assert "Command does not exist" in result.output

    run()
