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

import logging
import subprocess
import sys
import time
import threading
from typing import List

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
        dict(clients=1, delay=10, command="sleep 10s"),
        dict(clients=2, delay=10, command="sleep 10s"),
        dict(clients=5, delay=7, command="sleep 10s"),
    ),
    ids=lambda x: str(x),
)
def test_concurrent_commands(case, c8ydevice: Device):
    """Test running concurrent commands"""
    clients = case.get("clients")
    delay = case.get("delay", 0.1)
    command = case.get("command", "sleep 10s")

    threads: List[threading.Thread] = []
    results: List[subprocess.CompletedProcess] = [None] * clients
    durations: List[float] = [None] * clients

    for i in range(0, clients):

        cmd_args = (
            "plugin",
            "command",
            c8ydevice.device,
            "--",
            command,
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
