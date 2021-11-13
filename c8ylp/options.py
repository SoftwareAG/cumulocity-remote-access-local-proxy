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
        return value

    click.echo(f"Loading env-file: {value}")
    if os.path.exists(value):
        loadenv(value)
    else:
        logging.info("env file does not exist: %s", value)
    return value


def deactivate_prompts(ctx: click.Context, _param: click.Parameter, value: Any):
    """Deactivate all prompts

    Args:
        ctx (click.Context): Click Context
        _param (click.Parameter): Click Parameter
        value (Any): Parameter value

    Returns:
        Any: Parameter value
    """
    if value:
        for i_param in ctx.command.params:
            if isinstance(i_param, click.Option) and i_param.prompt is not None:
                i_param.prompt = None
    return value


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

    host = ctx.params.get("host")

    if not host:
        return value

    if not value:
        return value

    if isinstance(value, tuple):
        return value

    client = CumulocityClient(hostname=host, token=value)

    try:
        client.validate_credentials()
        click.secho("Validating detected c8y token: ", nl=False)
        click.secho("OK", fg="green")
    except Exception:
        click.secho("Validating detected c8y token: ", nl=False)
        click.secho("INVALID", fg="red")
        logging.warning(
            "Token is no longer valid for host %s. The token will be ignored", host
        )
        return ""
    return value


HOSTNAME = click.option(
    # "--hostname",
    "--host",
    "host",
    is_eager=True,
    prompt=True,
    callback=lazy_required,
    envvar=("C8Y_HOST", "C8Y_BASEURL", "C8Y_URL"),
    help="Cumulocity Hostname  [required]",
)


ARG_DEVICE = click.argument(
    "device",
    nargs=1,
    required=True,
)

DEVICE = click.option(
    "--device",
    "-d",
    required=False,
    envvar="C8YLP_DEVICE",
    show_envvar=True,
    help="Device external identity",
)

EXTERNAL_IDENTITY_TYPE = click.option(
    "--external-type",
    envvar="C8YLP_EXTERNAL_TYPE",
    default="c8y_Serial",
    show_default=True,
    show_envvar=True,
    help="external Id Type",
)

REMOTE_ACCESS_TYPE = click.option(
    "--config",
    "-c",
    required=False,
    envvar="C8YLP_CONFIG",
    default="Passthrough",
    show_default=True,
    show_envvar=True,
    help="name of the C8Y Remote Access Configuration",
)

C8Y_TENANT = click.option(
    "--tenant", "-t", envvar="C8Y_TENANT", help="Cumulocity tenant id", show_envvar=True
)

C8Y_USER = click.option(
    "--user",
    "-u",
    envvar=("C8Y_USER", "C8Y_USERNAME"),
    show_envvar=True,
    help="Cumulocity username",
)

C8Y_TOKEN = click.option(
    "--token",
    "-t",
    callback=validate_token,
    envvar="C8Y_TOKEN",
    is_eager=True,
    show_envvar=True,
    help="Cumulocity token",
)

C8Y_PASSWORD = click.option(
    "--password",
    "-p",
    envvar="C8Y_PASSWORD",
    prompt=False,
    hide_input=True,
    show_envvar=True,
    help="Cumulocity password",
)

C8Y_TFA_CODE = click.option(
    "--tfa-code",
    envvar="C8Y_TFA_CODE",
    show_envvar=True,
    help="TFA Code. Required when the 'TFA enabled' is enabled for a user",
)

PORT = click.option(
    "--port",
    type=int,
    callback=lambda ctx, param, value: get_unused_port() if value < 1 else value,
    default=2222,
    envvar="C8YLP_PORT",
    show_envvar=True,
    show_default=True,
    help="TCP Port which should be opened. 0=Random port",
)

PORT_DEFAULT_RANDOM = click.option(
    "--port",
    type=int,
    callback=lambda ctx, param, value: get_unused_port() if value < 1 else value,
    default=0,
    envvar="C8YLP_PORT",
    show_default=True,
    show_envvar=True,
    help="TCP Port which should be opened. 0=Random port",
)

PING_INTERVAL = click.option(
    "--ping-interval",
    type=int,
    default=0,
    show_default=True,
    show_envvar=True,
    envvar="C8YLP_PING_INTERVAL",
    help="Websocket ping interval in seconds. 0=disabled",
)

KILL_EXISTING = click.option(
    "--kill",
    "-k",
    envvar="C8YLP_KILL",
    show_envvar=True,
    help="Kills all existing processes of c8ylp",
)


TCP_SIZE = click.option(
    "--tcp-size",
    envvar="C8YLP_TCP_SIZE",
    default=4096,
    show_default=True,
    show_envvar=True,
    help="TCP Package Size",
)

TCP_TIMEOUT = click.option(
    "--tcp-timeout",
    envvar="C8YLP_TCP_TIMEOUT",
    default=0,
    show_default=True,
    show_envvar=True,
    help="Timeout in sec. for inactivity. Can be activited with values > 0",
)

LOGGING_VERBOSE = click.option(
    "--verbose",
    "-v",
    envvar="C8YLP_VERBOSE",
    is_flag=True,
    default=False,
    help="Print Debug Information into the Logs and Console when set",
)

STORE_TOKEN = click.option(
    "--store-token",
    "store_token",
    envvar="C8YLP_STORE_TOKEN",
    is_flag=True,
    default=True,
    help="Store the Cumulocity host, tenant and token to the env-file if a file is being used",
)


MODE_SCRIPT = click.option(
    "--script-mode",
    "-s",
    envvar="C8YLP_SCRIPT_MODE",
    is_flag=True,
    default=False,
    help="Stops the TCP Server after first connection. No automatical restart!",
)

DISABLE_PROMPT = click.option(
    "--disable-prompts",
    "-d",
    "disable_prompts",
    envvar="C8YLP_DISABLE_PROMPTS",
    default=False,
    is_eager=True,
    is_flag=True,
    expose_value=True,
    callback=deactivate_prompts,
)

SSL_IGNORE_VERIFY = click.option(
    "--ignore-ssl-validate",
    envvar="C8YLP_IGNORE_SSL_VALIDATE",
    is_flag=True,
    default=False,
    help="Ignore Validation for SSL Certificates while connecting to Websocket",
)

PID_USE = click.option(
    "--use-pid",
    envvar="C8YLP_USE_PID",
    is_flag=True,
    default=False,
    help="Will create a PID-File to store all Processes currently running (see --pidfile for the location)",
)

PID_FILE = click.option(
    "--pid-file",
    envvar="C8YLP_PID_FILE",
    default=lambda: pathlib.Path("~/.c8ylp/c8ylp").expanduser()
    if os.name == "nt"
    else "/var/run/c8ylp",
    show_default=True,
    show_envvar=True,
    help="PID-File file location to store all Processes currently running",
)

SERVER_RECONNECT_LIMIT = click.option(
    "--reconnects",
    envvar="C8YLP_RECONNECTS",
    type=int,
    default=5,
    show_default=True,
    show_envvar=True,
    callback=lambda c, p, v: -1 if c.params["script_mode"] else 5,
    help="number of reconnects to the Cloud Remote Service. 0 for infinite reconnects",
)

SSH_USER = click.option(
    "--ssh-user",
    envvar="C8YLP_SSH_USER",
    type=str,
    required=True,
    prompt=True,
    help="Start an interactive ssh session with the given user",
)

ARG_SSH_COMMAND = click.argument("command", nargs=1, required=True)

ARG_SCRIPT = click.argument(
    "script", type=click.Path(resolve_path=True), nargs=1, required=True
)


ENV_FILE = click.option(
    "--env-file",
    "env_file",
    envvar="C8YLP_ENV_FILE",
    is_eager=True,
    expose_value=True,
    type=click.Path(
        exists=True,
    ),
    callback=load_envfile,
    help="Environment file to load. Any settings loaded via this file will control other parameters",
)

ENV_FILE_OPTIONAL_EXISTS = click.option(
    "--env-file",
    "env_file",
    envvar="C8YLP_ENV_FILE",
    is_eager=True,
    expose_value=True,
    required=True,
    type=click.Path(
        exists=False,
    ),
    callback=load_envfile,
    help="Environment file to load. Any settings loaded via this file will control other parameters",
)
