"""Test plugin command"""

import logging
import subprocess
import time
import threading
from typing import List

import pytest

from .fixtures import Device


def proxy_cli(*args) -> subprocess.CompletedProcess:
    """Execute the proxy cli command with given arguments"""
    return subprocess.run(
        [
            "python",
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
