"""Options"""

#  Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
#  SPDX-License-Identifier: Apache-2.0
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import logging
import os
import pathlib
import sys
from typing import Any

import click

from c8ylp.env import loadenv
from c8ylp.helper import get_unused_port
from c8ylp.rest_client.c8yclient import CumulocityClient


def load_envfile(ctx: click.Context, _param: click.Parameter, value: Any):
    """Load environment variables from a file

    Args:
        ctx (click.Context): Click context
        _param (click.Parameter): Click parameter
        value (Any): Parameter value
    """
    if not value or ctx.resilient_parsing:
        return

    click.echo(f"Loading env-file: {value}")
    loadenv(value)


def lazy_required(ctx: click.Context, _param: click.Parameter, value: Any):
    """Apply lazy command argument parsing so that if a parameter is marked
    as eager, it will only raise a MissingParameter exception if --help or
    --version has not been specified (regardless of the order)

    Args:
        ctx (click.Context): Click Context
        param (click.Parameter): Click Parameter
        value (Any): Parameter value

    Raises:
        click.MissingParameter: Missing parameter exception

    Returns:
        Any: Parameter value
    """
    # Ignore error if help or version are being displayed
    # using original sys.argv as the other click args may not have
    # been procssed yet.
    if "--help" in sys.argv or "--version" in sys.argv:
        return None

    if ctx.resilient_parsing:
        return None

    if not value:
        raise click.MissingParameter()

    return value


def validate_token(ctx: click.Context, _param, value) -> Any:
    """Validate Cumulocity token. If it is invalid then it
    will be ignored.

    Args:
        ctx (Any): Click context
        _param (Any): Click param
        value (Any): Parameter value

    Returns:
        Any: Parameter value
    """
    if not value or ctx.resilient_parsing:
        return None

    hostname = ctx.params.get("hostname")

    if not hostname:
        return value

    if not value:
        return value

    if isinstance(value, tuple):
        return value

    client = CumulocityClient(hostname=hostname, token=value)

    try:
        client.validate_credentials()
        click.secho("Validating detected c8y token: ", nl=False)
        click.secho("OK", fg="green")
    except Exception:
        click.secho("Validating detected c8y token: ", nl=False)
        click.secho("INVALID", fg="red")
        logging.warning(
            "Token is no longer valid for host %s. The token will be ignored", hostname
        )
        return ""
    return value


HOSTNAME = click.option(
    # "--hostname",
    "--host",
    "-h",
    "host",
    is_eager=True,
    callback=lazy_required,
    envvar=("C8Y_HOST", "C8Y_BASEURL", "C8Y_URL"),
    help="Cumulocity Hostname  [required]",
)

DEVICE = click.option(
    "--device",
    "-d",
    required=True,
    envvar="C8Y_DEVICE",
    help="Device external identity",
)

EXTERNAL_IDENTITY_TYPE = click.option(
    "--external-type",
    envvar="C8Y_EXTERNAL_TYPE",
    default="c8y_Serial",
    help="external Id Type",
)

REMOTE_ACCESS_TYPE = click.option(
    "--config",
    "-c",
    required=True,
    envvar="C8Y_CONFIG",
    default="Passthrough",
    help="name of the C8Y Remote Access Configuration",
)

C8Y_TENANT = click.option(
    "--tenant", "-t", envvar="C8Y_TENANT", help="Cumulocity tenant id"
)

C8Y_USER = click.option(
    "--user",
    "-u",
    envvar=("C8Y_USER", "C8Y_USERNAME"),
    help="Cumulocity username",
)

C8Y_TOKEN = click.option(
    "--token",
    "-t",
    callback=validate_token,
    envvar="C8Y_TOKEN",
    is_eager=True,
    help="Cumulocity token",
)

C8Y_PASSWORD = click.option(
    "--password",
    "-p",
    envvar="C8Y_PASSWORD",
    prompt=False,
    hide_input=True,
    help="Cumulocity password",
)

C8Y_TFACODE = click.option(
    "--tfa-code",
    envvar="C8Y_TFACODE",
    help="TFA Code when an user with the Option 'TFA enabled' is used",
)

PORT = click.option(
    "--port",
    envvar="C8Y_PORT",
    type=int,
    callback=lambda ctx, param, value: get_unused_port() if value < 1 else value,
    default=2222,
    help="TCP Port which should be opened. 0=Random port",
)

PING_INTERVAL = click.option(
    "--ping-interval",
    envvar="C8Y_PING_INTERVAL",
    type=int,
    default=0,
    help="Websocket ping interval in seconds. 0=disabled",
)

KILL_EXISTING = click.option(
    "--kill", "-k", help="Kills all existing processes of c8ylp"
)


TCP_SIZE = click.option(
    "--tcp-size", envvar="C8Y_TCPSIZE", default=4096, help="TCP Package Size"
)

TCP_TIMEOUT = click.option(
    "--tcp-timeout",
    envvar="C8Y_TCPTIMEOUT",
    default=0,
    help="Timeout in sec. for inactivity. Can be activited with values > 0",
)

LOGGING_VERBOSE = click.option(
    "--verbose",
    "-v",
    envvar="VERBOSE",
    is_flag=True,
    default=False,
    help="Print Debug Information into the Logs and Console when set",
)

MODE_SCRIPT = click.option(
    "--scriptmode",
    "-s",
    envvar="C8Y_SCRIPTMODE",
    is_flag=True,
    default=False,
    help="Stops the TCP Server after first connection. No automatical restart!",
)

SSL_IGNORE_VERIFY = click.option(
    "--ignore-ssl-validate",
    is_flag=True,
    default=False,
    help="Ignore Validation for SSL Certificates while connecting to Websocket",
)

PID_USE = click.option(
    "--use-pid",
    is_flag=True,
    default=False,
    help="Will create a PID-File to store all Processes currently running (see --pidfile for the location)",
)

PID_FILE = click.option(
    "--pidfile",
    default=lambda: pathlib.Path("~/.c8ylp/c8ylp").expanduser()
    if os.name == "nt"
    else "/var/run/c8ylp",
    help="PID-File file location to store all Processes currently running",
)

SERVER_RECONNECT_LIMIT = click.option(
    "--reconnects",
    type=int,
    default=5,
    callback=lambda c, p, v: -1 if c.params["scriptmode"] else 5,
    help="number of reconnects to the Cloud Remote Service. 0 for infinite reconnects",
)

SSH_USER = click.option(
    "--ssh-user",
    type=str,
    envvar="SSH_USER",
    required=True,
    help="Start an interactive ssh session with the given user",
)

SSH_COMMAND = click.option(
    "--command",
    "ssh_command",
    type=str,
    help="Execute a command via ssh then exit",
)

EXECUTE_SCRIPT = click.option(
    "--execute-script",
    type=str,
    help="Execute a script after the proxy has been started then exit",
)

ENV_FILE = click.option(
    "--env-file",
    default=None,
    is_eager=True,
    expose_value=False,
    type=click.Path(
        exists=True,
    ),
    callback=load_envfile,
    help="Environment file to load. Any settings loaded via this file will control other parameters",
)
