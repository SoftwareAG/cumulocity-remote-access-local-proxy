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
"""Provides cli helpers that can be used for usage with the local proxy in scripts.
"""
import logging
import time
import socket
import errno
from contextlib import contextmanager

import click


@contextmanager
def socketcontext(*args, **kw):
    """Socket context to ensure the socket is closed automatically when leaving the context"""
    sock = socket.socket(*args, **kw)
    try:
        yield sock
    finally:
        sock.close()


def wait_for_port(port: int, timeout: float = 30.0, silent: bool = False) -> None:
    """Wait for a port to be opened

    Args:
        port (int): Port number
        timeout (float): Timeout in seconds. Defaults to 30.0

    Raises:
        TimeoutError: Timeout error when the timeout period is exceeded
    """
    start_at = time.monotonic()
    expires_at = start_at + timeout
    while True:
        if is_port_open(port):
            duration = time.monotonic() - start_at
            if not silent:
                logging.info("Port is open. waited=%.3fs", duration)
            break

        if time.monotonic() >= expires_at:
            raise TimeoutError(
                f"Timed out waiting for port to be opened. port={port}, timeout={timeout}"
            )
        time.sleep(0.25)


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is open or not

    Args:
        port (int): Port number
        host (str): Host name

    Returns:
        bool: True if the port is open
    """
    with socketcontext() as sock:
        try:
            sock.bind((host, port))
        except OSError as ex:
            # port already in use error
            if ex.errno == errno.EADDRINUSE:
                return True

    return False


def get_unused_port() -> int:
    """Get a port which is currently unused"""
    with socketcontext() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
def cli():
    """Helper commands"""


@cli.command(name="wait")
@click.argument("port", type=click.IntRange(0, 65535))
@click.argument("timeout", type=click.FloatRange(0.0, 300.0))
@click.option("--silent", is_flag=True, help="Don't print out any error messages")
@click.pass_context
def cli_wait(ctx: click.Context, port, timeout, silent):
    """
    Wait for a port to be open

        \b
        PORT Port number to wait for
        TIMEOUT Timeout in seconds

    \b
    Example 1: Wait for port 2222 be open, but give up after 30 seconds

        \b
        python3 -m c8ylp.helper wait 2222 30

    """
    try:
        wait_for_port(port, timeout, silent)
    except TimeoutError:
        if not silent:
            click.secho(f"Port is not open after {timeout}s", fg="red")
        ctx.exit(1)


@cli.command(name="port")
def cli_port():
    """Get an unused port number

    Please note it does not guarantee that the port will not be taken by another application

    \b
    Example 1: Get a random unused port

        \b
        python3 -m c8ylp.helper port

    """
    click.echo(get_unused_port())


if __name__ == "__main__":
    cli()
