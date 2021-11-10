#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from enum import IntEnum
import logging
import os
import pathlib
import sys
import signal
from logging.handlers import RotatingFileHandler
import platform
import dataclasses
import click

from c8ylp.rest_client.c8yclient import CumulocityClient
from c8ylp.tcp_socket.tcp_server import TCPServer
from c8ylp.websocket_client.ws_client import WebsocketClient
from c8ylp.helper import get_unused_port


class ExitCodes(IntEnum):
    """Exit codes"""

    OK = 0
    NO_SESSION = 2
    NOT_AUTHORIZED = 3
    PID_FILE_ERROR = 4


class ExitCommand(Exception):
    """ExitCommand error"""


def signal_handler(signal, frame):
    raise ExitCommand()


def validate_token(ctx, param, value):
    click.echo("Validating existing token")
    if isinstance(value, tuple):
        return value

    hostname = ctx.params.get("hostname")

    client = CumulocityClient(hostname=hostname, token=value)

    try:
        client.validate_credentials()
    except:
        logging.warning(
            f"Token is no longer valid for host {hostname}. The token will be ignored"
        )
        return ""
    return value


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    from c8ylp import __version__

    click.echo(f"Version {__version__}")
    ctx.exit(ExitCodes.OK)


@click.command()
@click.option(
    "--hostname",
    "-h",
    is_eager=True,
    required=True,
    envvar="C8Y_HOST",
    help="Cumulocity Hostname",
)
@click.option(
    "--device",
    "-d",
    required=True,
    envvar="C8Y_DEVICE",
    help="Device external identity",
)
@click.option(
    "--extype", envvar="C8Y_EXTYPE", default="c8y_Serial", help="external Id Type"
)
@click.option(
    "--config",
    "-c",
    required=True,
    envvar="C8Y_CONFIG",
    default="Passthrough",
    help="name of the C8Y Remote Access Configuration",
)
@click.option("--tenant", "-t", envvar="C8Y_TENANT", help="Cumulocity tenant id")
@click.option(
    "--user",
    "-u",
    envvar="C8Y_USER",
    help="Cumulocity username",
)
@click.option(
    "--token",
    "-t",
    callback=validate_token,
    envvar="C8Y_TOKEN",
    is_eager=True,
    help="Cumulocity token",
)
@click.option(
    "--password",
    "-p",
    envvar="C8Y_PASSWORD",
    prompt=False,
    hide_input=True,
    help="Cumulocity password",
)
@click.option(
    "--tfacode",
    envvar="C8Y_TFACODE",
    help="TFA Code when an user with the Option 'TFA enabled' is used",
)
@click.option(
    "--port",
    envvar="C8Y_PORT",
    type=int,
    callback=lambda ctx, param, value: get_unused_port() if value < 1 else value,
    default=2222,
    help="TCP Port which should be opened",
)
@click.option(
    "--ping-interval",
    envvar="C8Y_PING_INTERVAL",
    type=int,
    default=0,
    help="Websocket ping interval in seconds. 0=disabled",
)
@click.option("--kill", "-k", help="Kills all existing processes of c8ylp")
@click.option("--tcpsize", envvar="C8Y_TCPSIZE", default=4096, help="TCP Package Size")
@click.option(
    "--tcptimeout",
    envvar="C8Y_TCPTIMEOUT",
    default=0,
    help="Timeout in sec. for inactivity. Can be activited with values > 0",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Print Debug Information into the Logs and Console when set",
)
@click.option(
    "--scriptmode",
    "-s",
    is_flag=True,
    default=False,
    help="Stops the TCP Server after first connection. No automatical restart!",
)
@click.option(
    "--ignore-ssl-validate",
    is_flag=True,
    default=False,
    help="Ignore Validation for SSL Certificates while connecting to Websocket",
)
@click.option(
    "--use-pid",
    is_flag=True,
    default=False,
    help="Will create a PID-File in /var/run/c8ylp to store all Processes currently running",
)
@click.option(
    "--pidfile",
    default=lambda: pathlib.Path("~/.c8ylp/c8ylp").expanduser()
    if os.name == "nt"
    else "/var/run/c8ylp",
    help="PID-File file location to store all Processes currently running",
)
@click.option(
    "--reconnects",
    type=int,
    default=5,
    callback=lambda c, p, v: -1 if c.params["scriptmode"] else 5,
    help="number of reconnects to the Cloud Remote Service. 0 for infinite reconnects",
)
@click.pass_context
@click.option(
    "--version",
    is_flag=True,
    default=False,
    required=False,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Show version number",
)
def cli(
    ctx,
    hostname,
    device,
    extype,
    config,
    tenant,
    user,
    token,
    password,
    tfacode,
    port,
    ping_interval,
    kill,
    tcpsize,
    tcptimeout,
    verbose,
    scriptmode,
    ignore_ssl_validate,
    use_pid,
    pidfile,
    reconnects,
):
    click.echo(locals())
    options = ProxyOptions().fromdict(locals())
    options.validate()
    start(ctx, options)


@dataclasses.dataclass
class ProxyOptions:
    hostname = ""
    device = ""
    extype = ""
    config = ""
    tenant = ""
    user = ""
    token = ""
    password = ""
    tfacode = ""
    port = 0
    ping_interval = ""
    kill = ""
    tcpsize = ""
    tcptimeout = ""
    verbose = False
    scriptmode = False
    ignore_ssl_validate = False
    use_pid = False
    pidfile = ""
    reconnects = 0

    def fromdict(self, d):
        assert isinstance(d, dict)
        for key, value in d.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def validate(self) -> bool:
        if self.token:
            return True

        # if not (self.user and self.password):
        #     raise click.BadParameter(
        #         "--user and --password are required when not using a token"
        #     )

        return True


def configure_logger(path: str = None, verbose: bool = False):
    if not path:
        path = pathlib.Path.home() / ".c8ylp"
        path.mkdir(parents=True, exist_ok=True)

    loglevel = logging.DEBUG if verbose else logging.WARNING
    logger = logging.getLogger()
    logger.setLevel(loglevel)
    log_file_formatter = logging.Formatter(
        "%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s"
    )
    log_console_formatter = logging.Formatter("[c8ylp] %(levelname)-8s %(message)s")

    # Set default log format
    if len(logger.handlers) == 0:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_console_formatter)
        console_handler.setLevel(loglevel)
        logger.addHandler(console_handler)
    else:
        handler = logger.handlers[0]
        handler.setFormatter(log_console_formatter)

    # Max 5 log files each 10 MB.
    rotate_handler = RotatingFileHandler(
        filename=path / "localproxy.log", maxBytes=10000000, backupCount=5
    )
    rotate_handler.setFormatter(log_file_formatter)
    rotate_handler.setLevel(loglevel)
    # Log to Rotating File
    logger.addHandler(rotate_handler)
    return logger


def create_client(ctx: click.Context, opts: ProxyOptions):
    client = CumulocityClient(
        hostname=opts.hostname,
        tenant=opts.tenant,
        user=opts.user,
        password=opts.password,
        tfacode=opts.tfacode,
        token=opts.token,
        ignore_ssl_validate=opts.ignore_ssl_validate,
    )
    client.validate_tenant_id()

    retries = 2
    success = False
    while retries:
        try:
            if client.token:
                client.validate_credentials()
            else:
                client.login_oauth()

            success = True
            break
        except Exception as ex:
            logging.info(ex)

            if not opts.scriptmode:
                if not client.password:
                    client.password = click.prompt(
                        text="Enter your Password", hide_input=True
                    )

                if not client.tfacode:
                    client.tfacode = click.prompt(
                        text="Enter your TFA-Token", hide_input=False
                    )
        retries -= 1

    if not success:
        ctx.exit(ExitCodes.NO_SESSION)

    return client


def get_config_id(mor, config):
    if "c8y_RemoteAccessList" not in mor:
        device = mor["name"]
        logging.error(
            f'No Remote Access Configuration has been found for device "{device}"'
        )
        sys.exit(1)
    access_list = mor["c8y_RemoteAccessList"]
    device = mor["name"]
    config_id = None
    for remote_access in access_list:
        if not remote_access["protocol"] == "PASSTHROUGH":
            continue
        if config and remote_access["name"] == config:
            config_id = remote_access["id"]
            logging.info(
                f'Using Configuration with Name "{config}" and Remote Port {remote_access["port"]}'
            )
            break
        if not config:
            config_id = remote_access["id"]
            logging.info(
                f'Using Configuration with Name "{config}" and Remote Port {remote_access["port"]}'
            )
            break
    if not config_id:
        if config:
            logging.error(
                f'Provided config name "{config}" for "{device}" was not found or not of type "PASSTHROUGH"'
            )
            sys.exit(1)
        else:
            logging.error(
                f'No config of Type "PASSTHROUGH" has been found for device "{device}"'
            )
            sys.exit(1)
    return config_id


def start(ctx: click.Context, opts: ProxyOptions):
    if platform.system() in ("Linux", "Darwin"):
        signal.signal(signal.SIGUSR1, signal_handler)
    else:
        signal.signal(signal.SIGINT, signal_handler)

    configure_logger(verbose=opts.verbose)

    if opts.use_pid:
        try:
            upsert_pid_file(
                opts.pidfile, opts.device, opts.hostname, opts.config, opts.user
            )
        except PermissionError:
            ctx.exit(ExitCodes.PID_FILE_ERROR)
    if opts.kill:
        if opts.use_pid:
            kill_existing_instances(opts.pidfile)
        else:
            logging.warning(
                f'WARNING: Killing existing instances is only supported when "--use-pid" is used.'
            )

    client = create_client(ctx, opts)
    mor = client.get_managed_object(opts.device, opts.extype)
    config_id = get_config_id(mor, opts.config)
    device_id = client.get_device_id(mor)

    is_authorized = client.validate_remote_access_role()
    if not is_authorized:
        logging.error(
            f"User {opts.user} is not authorized to use Cloud Remote Access. Contact your Cumulocity Admin!"
        )
        ctx.exit(ExitCodes.NOT_AUTHORIZED)

    client_opts = {
        "host": opts.hostname,
        "config_id": config_id,
        "device_id": device_id,
        "session": client.session,
        "token": opts.token,
        "ignore_ssl_validate": opts.ignore_ssl_validate,
        "reconnects": opts.reconnects,
        "ping_interval": opts.ping_interval,
    }
    websocket_client = WebsocketClient(**client_opts)
    wst = websocket_client.connect()
    tcp_server = TCPServer(
        opts.port,
        websocket_client,
        opts.tcpsize,
        opts.tcptimeout,
        wst,
        opts.scriptmode,
    )
    # TCP is blocking...
    websocket_client.tcp_server = tcp_server
    try:
        tcp_server.start()
    except Exception as ex:
        logging.error(f"Error on TCP-Server {ex}")
    finally:
        if opts.use_pid:
            clean_pid_file(opts.pidfile)
        tcp_server.stop()
        ctx.exit(ExitCodes.OK)


def upsert_pid_file(pidfile, device, url, config, user):
    try:
        clean_pid_file(pidfile)
        pid_file_text = get_pid_file_text(device, url, config, user)
        logging.debug(f"Adding {pid_file_text} to PID-File {pidfile}")
        if not os.path.exists(pidfile):
            if not os.path.exists(os.path.dirname(pidfile)):
                os.makedirs(os.path.dirname(pidfile))
            file = open(pidfile, "w")
            file.seek(0)
        else:
            file = open(pidfile, "a+")
            file.seek(0)
        file.write(pid_file_text)
        file.write("\n")
    except PermissionError:
        logging.error(
            f"Could not write PID-File {pidfile}. Please create the folder manually and assign the correct permissions."
        )
        raise


def get_pid_file_text(device, url, config, user):
    pid = str(os.getpid())
    return f"{pid},{url},{device},{config},{user}"


def get_pid_from_line(line):
    return int(str.split(line, ",")[0])


def pid_is_active(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def clean_pid_file(pidfile, pid):
    if os.path.exists(pidfile):
        logging.debug(f"Cleaning Up PID {pid} in PID-File {pidfile}")
        pid = pid if pid is not None else os.getpid()
        with open(pidfile, "w+") as file:
            lines = file.readlines()
            file.seek(0)
            for line in lines:
                if get_pid_from_line(line) != pid:
                    file.write(line)
            file.truncate()

        if os.path.getsize(pidfile) == 0:
            os.remove(pidfile)


def kill_existing_instances(pidfile):
    if os.path.exists(pidfile):
        with open(pidfile) as file:
            pid = int(os.getpid())
            for line in file:
                other_pid = get_pid_from_line(line)
                if pid != other_pid and pid_is_active(other_pid):
                    logging.info(f"Killing other running Process with PID {other_pid}")
                    os.kill(get_pid_from_line(line), 9)
                clean_pid_file(pidfile, other_pid)


if __name__ == "__main__":
    sys.exit(cli())
