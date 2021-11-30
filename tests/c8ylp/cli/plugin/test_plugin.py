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
"""Plugin run"""

import platform
import os
import stat
from pathlib import Path

import pytest

import responses
from click.testing import CliRunner
from c8ylp.main import cli
from c8ylp.cli.core import ExitCodes
from tests.env import Environment
from tests.fixtures import FixtureCumulocityAPI


def create_plugin(path: Path, code: str) -> str:
    """Format code to be unix compatible (i.e. strip \\r characters)
    Note: Path.write_text does not work as it does not allow to set the
    newline character (but this seems to be fixed in Python 3.10)

    Args:
        path (Path): Path to the script to be written to
        code (str): Code to be formatted

    Returns:
        str: Unix friendly code
    """
    with path.open("w", newline="\n") as file:
        file.write(code.replace("\r", "", -1))


@pytest.fixture(name="plugin")
def plugin_fixture(tmpdir):
    """Proxy plugin fixture which creates a temporary plugin folder"""
    plugin_folder = Path(tmpdir) / ".c8ylp" / "plugins"
    plugin_folder.mkdir(parents=True, exist_ok=True)
    yield plugin_folder


def test_plugin_list(
    plugin: Path,
):
    """Test getting a list of the plugins"""

    # Simulate some plugins
    bash_plugin_1 = Path(plugin / "launch.sh")
    bash_plugin_1.touch()

    bash_plugin_2 = Path(plugin / "scp.sh")
    bash_plugin_2.touch()

    py_plugin_1 = Path(plugin / "mycommand.sh")
    py_plugin_1.touch()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["plugin"],
        env={
            "C8YLP_PLUGINS": str(plugin),
        },
    )

    assert result.exit_code == ExitCodes.OK
    subcommands = []
    found = False

    for line in result.output.splitlines():
        if found:
            name, _, _ = line.strip().partition(" ")
            subcommands.append(name)
        if "Commands:" in line:
            found = True

    assert subcommands == ["command", "launch", "mycommand", "scp"]


def test_calling_unknown_plugin(
    plugin: Path,
):
    """Test calling an unknown plugin"""

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["plugin", "doesnotexist"],
        env={
            "C8YLP_PLUGINS": str(plugin),
        },
    )

    assert result.exit_code == ExitCodes.PLUGIN_NOT_FOUND


def test_bash_plugin(
    plugin: Path,
    c8yserver: FixtureCumulocityAPI,
    env: Environment,
    capfd: pytest.CaptureFixture,
):
    """Test bash plugin"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        port = "2223"
        c8yserver.simulate_pre_authenticated(serial)

        bash_plugin_1 = Path(plugin / "launch.sh")

        create_plugin(
            bash_plugin_1,
            """
        #!/bin/bash
        echo "Running my custom launcher: PORT=$PORT, DEVICE=$DEVICE"
        """.lstrip(),
        )

        # make plugin executable
        exiting_stat = os.stat(bash_plugin_1)
        os.chmod(bash_plugin_1, exiting_stat.st_mode | stat.S_IEXEC)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "plugin",
                "launch",
                "--port",
                port,
                serial,
            ],
            env={
                **env.create_authenticated(),
                "C8YLP_PLUGINS": str(plugin),
            },
        )

        assert result.exit_code == ExitCodes.OK

        out, _ = capfd.readouterr()
        assert out == f"Running my custom launcher: PORT={port}, DEVICE={serial}\n"

    run()


@pytest.mark.skipif(
    platform.system() == "Windows", reason="Windows does not throw an error"
)
def test_invalid_bash_plugin(
    plugin: Path,
    c8yserver: FixtureCumulocityAPI,
    env: Environment,
):
    """Test invalid bash plugin"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        port = "2223"
        c8yserver.simulate_pre_authenticated(serial)

        bash_plugin_1 = Path(plugin / "launch.sh")

        create_plugin(
            bash_plugin_1,
            """

        # Plugin which is missing the shebang!
        echo "Running my customer launcher: PORT=$PORT"
        """,
        )

        # make plugin executable
        existing_stat = os.stat(bash_plugin_1)
        os.chmod(bash_plugin_1, existing_stat.st_mode | stat.S_IEXEC)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "plugin",
                "launch",
                "--port",
                port,
                serial,
            ],
            env={
                **env.create_authenticated(),
                "C8YLP_PLUGINS": str(plugin),
            },
        )
        assert result.exit_code == ExitCodes.PLUGIN_EXECUTION_ERROR

    run()


@pytest.mark.parametrize(
    "code,exit_code",
    [
        (
            """
import click
    @click.command()
    def cli():
        print("Running plugin")
        """,
            ExitCodes.PLUGIN_INVALID_FORMAT,
        ),
        (
            """
import click
@click.command()
def invalid_name():
    print("Running plugin")
        """,
            ExitCodes.PLUGIN_INVALID_FORMAT,
        ),
        (
            """
import click
from c8ylp import options

@click.command()
@options.common_options
def cli(**kwargs):
    print("Running plugin")
        """,
            ExitCodes.OK,
        ),
    ],
    ids=["invalid indentation", "wrong func name", "OK"],
)
def test_invalid_python_plugin(
    code: str,
    exit_code: int,
    plugin: Path,
    c8yserver: FixtureCumulocityAPI,
    env: Environment,
):
    """Test invalid python plugin"""

    @responses.activate
    def run():
        serial = "ext-device-01"
        c8yserver.simulate_pre_authenticated(serial)

        plugin_1 = Path(plugin / "launch.py")
        create_plugin(plugin_1, code)

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "plugin",
                "launch",
                serial,
            ],
            env={
                **env.create_authenticated(),
                "C8YLP_PLUGINS": str(plugin),
            },
        )
        assert result.exit_code == exit_code

    run()
