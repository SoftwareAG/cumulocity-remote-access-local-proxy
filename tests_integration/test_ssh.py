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
"""Test plugin command"""

import subprocess
import sys

import pytest

from .fixtures import Device


def proxy_cli(*args) -> subprocess.CompletedProcess:
    """Execute the proxy cli command with given arguments"""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "c8ylp",
            *args,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


@pytest.mark.parametrize(
    "case",
    (
        dict(command="sleep 1s", exit_code=0),
        dict(command="sleep 1s; exit 111", exit_code=111),
        dict(command="sleep 1s; exit 111", user="unknown_user", exit_code=255),
    ),
    ids=lambda x: str(x),
)
def test_ssh_command_then_exit(case, c8ydevice: Device):
    """Test running a once off ssh command"""
    user = case.get("user", c8ydevice.ssh_user)
    command = case.get("command", "sleep 10s")

    result = proxy_cli(
        "connect",
        "ssh",
        c8ydevice.device,
        "--ssh-user",
        user,
        "--",
        command,
    )

    assert result.returncode == case.get("exit_code", 0)
