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
"""ssh. Used to start an interactive ssh session or execute a single ssh
command then exit.
"""

import logging
import os
import shutil
import subprocess
from typing import List

import click
from c8ylp import options
from c8ylp.cli.core import ExitCodes, ProxyContext


@click.command()
@options.common_options
@click.option(
    "--ssh-user",
    required=True,
    prompt=True,
    help="SSH username which is configured on the device",
)
@click.argument(
    "additional_args", metavar="[REMOTE_COMMANDS]...", nargs=-1, type=click.UNPROCESSED
)
@click.pass_context
def cli(ctx: click.Context, ssh_user: str, additional_args: List[str], **kwargs):
    """Start once-off proxy and connect via ssh

    An interactive ssh is opened if a remote command is not provided.

    Once the ssh session is closed, then the local proxy will be shutdown.

    Use "--" before the remote commands to prevent the arguments
    from being interpreted by c8ylp (i.e. to avoid clashes with c8ylp).

    \b
        DEVICE is the device's external identity

    Example 1: Start an interactive SSH connection

    \b
        c8ylp connect ssh device01 --env-file .env --ssh-user admin

    Example 2: Execute a command via SSH

    \b
        c8ylp connect ssh device01 --env-file .env --ssh-user admin -- systemctl status ssh

    Example 3: Execute a complex command via SSH (use quotes to ensure command is sent to the device)

    \b
        c8ylp connect ssh device01 --env-file .env --ssh-user admin -- "systemctl status ssh; dpkg --list | grep ssh"

    """
    proxy = ProxyContext(ctx, kwargs).start_background()

    if not shutil.which("ssh"):
        proxy.show_error(
            "ssh client not found. Please make sure the 'ssh' client is included in your PATH variable"
        )
        ctx.exit(ExitCodes.SSH_NOT_FOUND)

    device = proxy.device
    host = proxy.host

    ssh_args = [
        "ssh",
        "-o",
        "ServerAliveInterval=120",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-p",
        str(proxy.used_port),
        f"{ssh_user}@localhost",
    ]

    if additional_args:
        ssh_args.extend(additional_args)
        proxy.show_message(f"Executing command via ssh on {device} ({host})")
    else:
        proxy.show_message(f"Starting interactive ssh session with {device} ({host})")

    logging.info("Starting ssh session using: %s", " ".join(ssh_args))
    exit_code = subprocess.call(ssh_args, env=os.environ)
    if exit_code != 0:
        proxy.show_error(f"SSH exited with a non-zero exit code. code={exit_code}")
    ctx.exit(exit_code)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
