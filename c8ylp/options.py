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
"""Options"""

import logging
import os
from typing import Any
import functools

import click

from c8ylp.env import loadenv
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
    if os.path.exists(value) and os.path.isfile(value):
        loadenv(value)
    else:
        logging.info("env file does not exist or is not a file: %s", value)
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
        click.secho("Validating c8y token: ", nl=False)
        click.secho("OK", fg="green")
    except Exception:
        click.secho("Validating c8y token: ", nl=False)
        click.secho("EXPIRED/INVALID", fg="red")
        logging.info(
            "Token is no longer valid for host. The token will be ignored. host=%s",
            host,
        )
        return ""
    return value


HOSTNAME = click.option(
    "--host",
    "host",
    is_eager=True,
    prompt=False,
    envvar=("C8Y_HOST", "C8Y_BASEURL", "C8Y_URL"),
    help="Cumulocity Hostname  [required] [env var: C8Y_HOST]",
)

HOSTNAME_PROMPT = click.option(
    "--host",
    "host",
    is_eager=False,
    prompt=True,
    envvar=("C8Y_HOST", "C8Y_BASEURL", "C8Y_URL"),
    help="Cumulocity Hostname  [required] [env var: C8Y_HOST]",
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
    type=click.IntRange(0, 65535),
    default=2222,
    envvar="C8YLP_PORT",
    show_envvar=True,
    show_default=True,
    help="TCP Port which should be opened. 0=Random port",
)

PORT_DEFAULT_RANDOM = click.option(
    "--port",
    type=click.IntRange(0, 65535),
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

TCP_SIZE = click.option(
    "--tcp-size",
    envvar="C8YLP_TCP_SIZE",
    type=click.IntRange(1024, 8096 * 1024),
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
    help="Timeout in sec. for inactivity. Can be activated with values > 0",
)

LOGGING_VERBOSE = click.option(
    "--verbose",
    "-v",
    envvar="C8YLP_VERBOSE",
    is_flag=True,
    default=False,
    show_envvar=True,
    help="Print Debug Information into the Logs and Console when set",
)

STORE_TOKEN = click.option(
    "--store-token",
    "store_token",
    envvar="C8YLP_STORE_TOKEN",
    is_flag=True,
    default=True,
    show_envvar=True,
    help="Store the Cumulocity host, tenant and token to the env-file if a file is being used",
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
    show_envvar=True,
    callback=deactivate_prompts,
)

SSL_IGNORE_VERIFY = click.option(
    "--ignore-ssl-validate",
    envvar="C8YLP_IGNORE_SSL_VALIDATE",
    is_flag=True,
    default=False,
    show_envvar=True,
    help="Ignore Validation for SSL Certificates while connecting to Websocket",
)


SERVER_RECONNECT_LIMIT = click.option(
    "--reconnects",
    envvar="C8YLP_RECONNECTS",
    type=click.IntRange(-1, 10),
    default=5,
    show_default=True,
    show_envvar=True,
    help="number of reconnects to the Cloud Remote Service. 0 for infinite reconnects",
)

SSH_USER = click.option(
    "--ssh-user",
    envvar="C8YLP_SSH_USER",
    type=str,
    required=True,
    prompt=True,
    show_envvar=True,
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
    show_envvar=True,
    type=click.Path(
        exists=True,
    ),
    callback=load_envfile,
    help="Environment file to load. Any settings loaded via this file will control other options",
)

ENV_FILE_OPTIONAL_EXISTS = click.option(
    "--env-file",
    "env_file",
    envvar="C8YLP_ENV_FILE",
    is_eager=True,
    expose_value=True,
    show_envvar=True,
    required=False,
    type=click.Path(
        exists=False,
    ),
    callback=load_envfile,
    help="Environment file to load. Any settings loaded via this file will control other options",
)


def common_options(f):
    """Common Options"""
    options = [
        ARG_DEVICE,
        HOSTNAME,
        C8Y_TENANT,
        C8Y_USER,
        C8Y_TOKEN,
        C8Y_PASSWORD,
        C8Y_TFA_CODE,
        ENV_FILE,
        EXTERNAL_IDENTITY_TYPE,
        REMOTE_ACCESS_TYPE,
        PORT_DEFAULT_RANDOM,
        PING_INTERVAL,
        TCP_SIZE,
        TCP_TIMEOUT,
        LOGGING_VERBOSE,
        SSL_IGNORE_VERIFY,
        STORE_TOKEN,
        DISABLE_PROMPT,
        SERVER_RECONNECT_LIMIT,
    ]

    # Need to reverse the order to control the list order
    options = reversed(options)
    return functools.reduce(lambda x, opt: opt(x), options, f)
