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
"""SCP (Secure Copy) """

import filecmp
import logging
import subprocess
import sys
import time
import threading
from typing import List

import pytest

from .fixtures import Device, FileFactory


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
        {
            "size_mb": 1,
        },
    ),
    ids=lambda x: str(x),
)
def test_scp_file_transfer_roundtrip(
    case, c8ydevice: Device, file_factory: FileFactory
):
    """Test copy a file via scp to a remote device"""
    size_mb = case["size_mb"]
    name_prefix = f"dummyfile_{size_mb}"
    local_file = file_factory.create_file(name_prefix, size_mb)

    output = proxy_cli(
        "plugin",
        "command",
        c8ydevice.device,
        "--env-file",
        ".env",
        "--",
        "scp",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-P",
        "$PORT",
        str(local_file),
        f"{c8ydevice.ssh_user}@localhost:",
    )

    assert output.returncode == 0

    # Get file from device, and compare with the sent file
    roundtrip_file = file_factory.dir / f"{name_prefix}_roundtrip"
    output = proxy_cli(
        "plugin",
        "command",
        c8ydevice.device,
        "--",
        "scp",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-P",
        "$PORT",
        f"{c8ydevice.ssh_user}@localhost:/home/{c8ydevice.ssh_user}/{local_file.name}",
        str(roundtrip_file),
    )

    assert output.returncode == 0

    assert filecmp.cmp(local_file, roundtrip_file)


@pytest.mark.parametrize(
    "case",
    (
        dict(clients=1, delay=5, size_mb=10),
        dict(clients=2, delay=10, size_mb=10),
        dict(clients=2, delay=10, size_mb=100),
    ),
    ids=lambda x: str(x),
)
def test_concurrent_scp_commands(case, c8ydevice: Device, file_factory: FileFactory):
    clients = case.get("clients")
    delay = case.get("delay", 0.1)
    size_mb = case.get("size_mb", 10)
    name_prefix = f"concurrent_scp_{size_mb}"

    current_file = file_factory.create_file(name_prefix, size_mb)

    threads: List[threading.Thread] = []
    results: List[subprocess.CompletedProcess] = [None] * clients
    durations: List[float] = [None] * clients

    for i in range(0, clients):

        remote_file = f"{name_prefix}_client{i}.inttest"
        cmd_args = (
            "plugin",
            "command",
            c8ydevice.device,
            "--",
            "scp",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            "-P",
            "$PORT",
            str(current_file),
            f"{c8ydevice.ssh_user}@localhost:{remote_file}",
        )

        def run_proxy(index, *args):
            start = time.monotonic()
            results[index] = proxy_cli(*args)
            durations[index] = time.monotonic() - start
            logging.info(
                f"client={index+1}, exit_code={results[index].returncode} duration={int(durations[index])}"
            )

        thread = threading.Thread(target=run_proxy, args=[i, *cmd_args], daemon=True)
        thread.start()
        threads.append(thread)

        if i < clients - 1:
            time.sleep(delay)

    # wait for threads to finish
    for thread in threads:
        thread.join()

    assert [proc.returncode for proc in results] == [0] * clients
