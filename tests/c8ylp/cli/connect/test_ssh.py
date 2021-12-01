#
# Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""SSH command tests"""
import pathlib
from unittest.mock import Mock, patch

import pytest
import responses
from click.testing import CliRunner
from c8ylp.cli.core import PASSTHROUGH, REMOTE_ACCESS_FRAGMENT, ExitCodes
from c8ylp.main import cli
from tests.env import Environment
from tests.fixtures import FixtureCumulocityAPI


@patch("subprocess.call", return_value=0)
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
            ["connect", "ssh", serial, "--ssh-user", "example", "ls -la"],
            env=env.create_authenticated(),
        )

        mock_start_ssh.assert_called_once()
        assert result.exit_code == 0
        assert result.stdout

    run()


@patch("shutil.which", return_value=None)
def test_single_ssh_command_with_missing_ssh_binary(
    _mock_which: Mock, c8yserver: FixtureCumulocityAPI, env: Environment
):
    """Execute command via ssh then exit"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_pre_authenticated(serial)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["connect", "ssh", serial, "--ssh-user", "example", "ls -la"],
            env=env.create_authenticated(),
        )

        assert result.exit_code == ExitCodes.SSH_NOT_FOUND

    run()


# @patch("c8ylp.plugins.ssh.subprocess.call", return_code=0)
@patch("subprocess.call", return_value=0)
def test_launching_ssh_with_fixed_port(
    mock_call: Mock, c8yserver: FixtureCumulocityAPI, env: Environment
):
    """Execute command via ssh client using a specific port"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        port = "1234"
        username = "admin"
        c8yserver.simulate_pre_authenticated(serial)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "connect",
                "ssh",
                serial,
                "--port",
                port,
                "--ssh-user",
                username,
                "ls -la",
            ],
            env=env.create_authenticated(),
        )

        assert result.exit_code == ExitCodes.OK
        mock_call.assert_called_once()
        ssh_cmd = mock_call.call_args[0][0]

        assert ssh_cmd == [
            "ssh",
            "-o",
            "ServerAliveInterval=120",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-p",
            port,
            f"{username}@localhost",
            "ls -la",
        ]

        assert mock_call.call_args[1]["env"]

    run()


@patch("subprocess.call", return_value=99)
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
                "connect",
                "ssh",
                serial,
                "--verbose",
                "--ssh-user",
                "example",
                "ls -l /etc; exit 99",
            ],
            env=env.create_authenticated(),
        )
        assert result.exit_code == 99
        assert result.stdout

        mock_start_ssh.assert_called_once()
        ssh_args = mock_start_ssh.call_args[0][0]
        assert "ls -l /etc; exit 99" in ssh_args
        assert "example@localhost" in ssh_args

    run()


@patch("subprocess.call", return_value=0)
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
            cli, ["connect", "ssh", serial, "ls -la"], env=test_env, input="admin"
        )

        mock_start_ssh.assert_called_once()
        assert result.exit_code == 0
        assert result.stdout
        ssh_args = mock_start_ssh.call_args[0][0]
        assert "admin@localhost" in ssh_args

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

        with patch("subprocess.call", return_value=0):
            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "connect",
                    "ssh",
                    serial,
                    "--env-file",
                    env_file.strpath,
                    "--ssh-user",
                    "admin",
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


def test_missing_role(c8yserver: FixtureCumulocityAPI, env: Environment):
    """Test: Command should fail if the user does not have the correct ROLE"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_pre_authenticated(serial_number=serial, roles=[])

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "connect",
                "ssh",
                serial,
                "--ssh-user",
                "admin",
            ],
            env=env.create_authenticated(),
        )

        assert result.exit_code == ExitCodes.MISSING_ROLE_REMOTE_ACCESS_ADMIN

    run()


@pytest.mark.parametrize(
    "case",
    (
        {
            "fragments": {},
            "exit_code": ExitCodes.DEVICE_MISSING_REMOTE_ACCESS_FRAGMENT,
        },
        {
            "description": "Missing PASSTHROUGH config",
            "fragments": {
                REMOTE_ACCESS_FRAGMENT: [
                    {"id": 1, "name": "example-ssh", "protocol": "ssh"}
                ]
            },
            "exit_code": ExitCodes.DEVICE_NO_PASSTHROUGH_CONFIG,
        },
        {
            "description": "Missing matching PASSTHROUGH name",
            "fragments": {
                REMOTE_ACCESS_FRAGMENT: [
                    {"id": 1, "name": "example-ssh", "protocol": "ssh"},
                    {"id": 2, "name": "custom-passthrough", "protocol": PASSTHROUGH},
                ]
            },
            "exit_code": ExitCodes.DEVICE_NO_MATCHING_PASSTHROUGH_CONFIG,
        },
        {
            "description": "Custom PASSTHROUGH name matching but still missing role",
            "fragments": {
                REMOTE_ACCESS_FRAGMENT: [
                    {"id": 1, "name": "example-ssh", "protocol": "ssh"},
                    {"id": 2, "name": "custom-passthrough", "protocol": PASSTHROUGH},
                ]
            },
            "options": ["--config", "custom-passthrough"],
            "exit_code": ExitCodes.MISSING_ROLE_REMOTE_ACCESS_ADMIN,
        },
        {
            "description": "Custom PASSTHROUGH name matching but still missing role",
            "fragments": {
                REMOTE_ACCESS_FRAGMENT: [
                    {"id": 1, "name": "example-ssh", "protocol": "ssh"},
                    {"id": 2, "name": "custom-passthrough", "protocol": PASSTHROUGH},
                ]
            },
            "options": ["--config", ""],
            "exit_code": ExitCodes.MISSING_ROLE_REMOTE_ACCESS_ADMIN,
        },
    ),
)
def test_device_managed_object_permission_denied(
    case, c8yserver: FixtureCumulocityAPI, env: Environment
):
    """Test: Command should fail if the user does not have permission to read
    the device managed object
    """

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_pre_authenticated(
            serial_number=serial,
            # skip roles
            roles=[],
            device_managed_object=case["fragments"],
        )

        runner = CliRunner()
        args = [
            "connect",
            "ssh",
            serial,
            *case.get("options", []),
            "--ssh-user",
            "admin",
        ]

        result = runner.invoke(
            cli,
            args,
            env=env.create_authenticated(),
        )

        assert result.exit_code == case["exit_code"], case["description"]

    run()
