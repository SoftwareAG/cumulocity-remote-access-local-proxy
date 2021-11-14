"""SSH command tests"""
import pathlib
from unittest.mock import Mock, patch

import pytest
import responses
from click.testing import CliRunner
from c8ylp.main import ProxyOptions, cli
from tests.env import Environment
from tests.fixtures import FixtureCumulocityAPI


@patch("c8ylp.main.start_ssh", return_value=0)
def test_single_ssh_command_then_exit(
    mock_start_ssh: Mock, c8yserver: FixtureCumulocityAPI, env: Environment
):
    """Execute command via ssh then exit"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_pre_authenticated(serial)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["connect-ssh", serial, "--ssh-user", "example", "ls -la"],
            env=env.create_authenticated(),
        )

        mock_start_ssh.assert_called_once()
        assert result.exit_code == 0
        assert result.stdout

    run()


@patch("c8ylp.main.start_ssh", return_value=99)
def test_return_exit_code(
    mock_start_ssh: Mock, c8yserver: FixtureCumulocityAPI, env: Environment
):
    """Execute ssh command and resulting exit code is returned via c8ylp"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_pre_authenticated(serial)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "connect-ssh",
                serial,
                "--ssh-user",
                "example",
                "ls -l /etc; exit 99",
                "--verbose",
            ],
            env=env.create_authenticated(),
        )
        assert result.exit_code == 99
        assert result.stdout

        mock_start_ssh.assert_called_once()
        opts: ProxyOptions = mock_start_ssh.call_args[0][1]
        assert opts.ssh_user == "example"
        assert opts.additional_args == ("ls -l /etc; exit 99",)

    run()


@patch("c8ylp.main.start_ssh", return_value=0)
def test_prompt_for_ssh_user(
    mock_start_ssh, c8yserver: FixtureCumulocityAPI, env: Environment
):
    """Prompts for ssh user if it is not set via cli or env"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_pre_authenticated(serial_number=serial)

        runner = CliRunner()
        test_env = {
            **env.create_authenticated(),
            "C8YLP_SSH_USER": "",
        }
        result = runner.invoke(
            cli, ["connect-ssh", serial, "ls -la"], env=test_env, input="admin"
        )

        mock_start_ssh.assert_called_once()
        assert result.exit_code == 0
        assert result.stdout
        opts: ProxyOptions = mock_start_ssh.call_args[0][1]
        assert opts.ssh_user == "admin"

    run()


@pytest.mark.parametrize(
    "inputs",
    (
        {
            "stdin": [
                "12345\n",
            ],
            "env": {},
        },
        {
            "stdin": [],
            "env": {
                "C8Y_TFA_CODE": "000000",
            },
        },
    ),
)
def test_prompt_for_tfa(inputs, c8yserver: FixtureCumulocityAPI, tmpdir):
    """User is prompted for TFA code if the token is not provided"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_loginoptions(tenant="t12345")
        c8yserver.simulate_login_oauth(status_codes=[401, 200])
        c8yserver.simulate_current_user()
        c8yserver.simulate_external_identity(serial_number=serial)
        c8yserver.simulate_managed_object()

        env_file = tmpdir.join(".env")
        pathlib.Path(env_file).touch()
        stdin = "".join(inputs["stdin"])

        with patch("c8ylp.main.start_ssh", return_value=0):
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "connect-ssh",
                    serial,
                    "--ssh-user",
                    "admin",
                    "--env-file",
                    env_file.strpath,
                ],
                env={
                    "C8Y_HOST": "https://example.c8y.io",
                    "C8Y_TENANT": "t12345",
                    "C8Y_USER": "example-user",
                    "C8Y_PASSWORD": "d4mmy-p4s$wurd",
                    "C8Y_TOKEN": "",
                    **inputs["env"],
                },
                input=stdin,
            )

        assert result.exit_code == 0

        settings = {}
        for line in env_file.readlines():
            key, _, value = line.partition("=")
            settings[key] = value.rstrip("\n")

        # Password should not be stored, only the token
        assert settings == {
            "C8Y_HOST": "https://example.c8y.io",
            "C8Y_USER": "example-user",
            "C8Y_TENANT": "t12345",
            "C8Y_TOKEN": "dummy-token-xyz",
        }

    run()


def test_missing_role(c8yserver: FixtureCumulocityAPI, env: Environment, tmpdir):
    """Test: Command should fail if the user does not have the correct ROLE"""


def test_device_managed_object_permission_denied(
    c8yserver: FixtureCumulocityAPI, env: Environment, tmpdir
):
    """Test: Command should fail if the user does not have permission to read
    the device managed object
    """
