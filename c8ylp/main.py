#!/usr/bin/env python
"""Main cli interface to c8ylp"""
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

import dataclasses
import logging
import os
import pathlib
import platform
import signal
import shutil
import subprocess
import sys
import threading
import time
from datetime import timedelta
from enum import IntEnum
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, NoReturn

import click

from c8ylp import options

from c8ylp import __version__
from c8ylp.banner import BANNER1
from c8ylp.rest_client.c8yclient import CumulocityClient
from c8ylp.tcp_socket.tcp_server import TCPProxyServer
from c8ylp.websocket_client.ws_client import WebsocketClient


class ExitCodes(IntEnum):
    """Exit codes"""

    OK = 0
    NO_SESSION = 2
    NOT_AUTHORIZED = 3
    PID_FILE_ERROR = 4
    UNKNOWN = 9


class ExitCommand(Exception):
    """ExitCommand error"""


def signal_handler(_signal, _frame):
    """Signal handler"""
    raise ExitCommand()


def print_version(ctx: click.Context, _param: click.Parameter, value: Any) -> Any:
    """Print command version

    Args:
        ctx (click.Context): Click context
        _param (click.Parameter): Click param
        value (Any): Parameter value

    Returns:
        Any: Parameter value
    """
    if not value or ctx.resilient_parsing:
        return

    click.echo(f"Version {__version__}")
    ctx.exit(ExitCodes.OK)


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
    help="Cumulocity Remote Access Local Proxy",
)
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
@click.pass_context
def cli(ctx: click.Context):
    """Main cli entry point"""
    ctx.ensure_object(dict)
    if not ctx.invoked_subcommand:
        # Show help when no sub commands are called
        click.echo(ctx.get_help())


@cli.command(help="Start local proxy in server mode")
@options.ARG_DEVICE
# @options.DEVICE
@options.HOSTNAME
@options.EXTERNAL_IDENTITY_TYPE
@options.REMOTE_ACCESS_TYPE
@options.C8Y_TENANT
@options.C8Y_USER
@options.C8Y_TOKEN
@options.C8Y_PASSWORD
@options.C8Y_TFACODE
@options.PORT
@options.PING_INTERVAL
@options.KILL_EXISTING
@options.TCP_SIZE
@options.TCP_TIMEOUT
@options.LOGGING_VERBOSE
@options.MODE_SCRIPT
@options.SSL_IGNORE_VERIFY
@options.PID_USE
@options.PID_FILE
@options.SERVER_RECONNECT_LIMIT
@options.ENV_FILE
@click.pass_context
def start(
    ctx,
    *_args,
    **kwargs,
):
    """Main CLI command to start the local proxy server"""
    opts = ProxyOptions().fromdict(kwargs)
    start_proxy(ctx, opts)


@cli.command(help="Connect to a device via SSH")
@options.ARG_DEVICE
# @options.DEVICE
@options.HOSTNAME
@options.EXTERNAL_IDENTITY_TYPE
@options.REMOTE_ACCESS_TYPE
@options.C8Y_TENANT
@options.C8Y_USER
@options.C8Y_TOKEN
@options.C8Y_PASSWORD
@options.C8Y_TFACODE
@options.PORT
@options.PING_INTERVAL
@options.TCP_SIZE
@options.TCP_TIMEOUT
@options.LOGGING_VERBOSE
@options.SSL_IGNORE_VERIFY
@options.SSH_USER
@options.SSH_COMMAND
@options.ENV_FILE
@click.pass_context
def connect_ssh(
    ctx,
    *_args,
    **kwargs,
):
    """Main CLI command to start the local proxy server"""
    opts = ProxyOptions().fromdict(kwargs)
    opts.scriptmode = True
    start_proxy(ctx, opts)


@cli.command(
    "extension",
    help="""Run a custom extension which will start the local proxy, execute a script then exit
The script will have the following environment variables available to it:\n
 * DEVICE - external device identity\n
 * PORT   - port number of the local proxy
""",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@options.ARG_DEVICE
# @options.DEVICE
@options.HOSTNAME
@options.EXTERNAL_IDENTITY_TYPE
@options.REMOTE_ACCESS_TYPE
@options.C8Y_TENANT
@options.C8Y_USER
@options.C8Y_TOKEN
@options.C8Y_PASSWORD
@options.C8Y_TFACODE
@options.PORT
@options.PING_INTERVAL
@options.TCP_SIZE
@options.TCP_TIMEOUT
@options.LOGGING_VERBOSE
@options.SSL_IGNORE_VERIFY
@options.EXECUTE_SCRIPT
@options.ENV_FILE
@click.argument("script_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def extension(
    ctx,
    *_args,
    **kwargs,
):
    opts = ProxyOptions().fromdict(kwargs)
    opts.scriptmode = True
    logging.debug(f"Extra args: {opts.script_args}")
    start_proxy(ctx, opts)


@dataclasses.dataclass
class ProxyOptions:
    """Local proxy options"""

    host = ""
    device = ""
    external_type = ""
    config = ""
    tenant = ""
    user = ""
    token = ""
    password = ""
    tfa_code = ""
    port = 0
    ping_interval = ""
    kill = False
    tcp_size = 0
    tcp_timeout = 0
    verbose = False
    scriptmode = False
    ignore_ssl_validate = False
    use_pid = False
    pidfile = ""
    reconnects = 0
    ssh_user = ""
    ssh_command = ""
    execute_script = ""
    script_args = None

    def fromdict(self, src_dict: Dict[str, Any]) -> "ProxyOptions":
        """Load proxy settings from a dictionary

        Args:
            src_dict (Dict[str, Any]): [description]

        Returns:
            ProxyOptions: Proxy options after the values have been set
                via the dictionary
        """
        logging.info("Loading from dictionary")
        assert isinstance(src_dict, dict)
        for key, value in src_dict.items():
            logging.info("reading key: %s=%s", key, value)
            if hasattr(self, key):
                setattr(self, key, value)
        return self


def configure_logger(path: str = None, verbose: bool = False) -> logging.Logger:
    """Configure logger

    Args:
        path (str, optional): Path where the persistent logger should write to. Defaults to None.
        verbose (bool, optional): Use verbose logging. Defaults to False.

    Returns:
        logging.Logger: Created logger
    """
    if not path:
        path = pathlib.Path.home() / ".c8ylp"
        path.mkdir(parents=True, exist_ok=True)

    loglevel = logging.INFO if verbose else logging.WARNING
    logger = logging.getLogger()
    logger.setLevel(loglevel)
    log_file_formatter = logging.Formatter(
        "%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s"
    )
    log_console_formatter = logging.Formatter("[c8ylp]  %(levelname)-5s %(message)s")

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


def create_client(ctx: click.Context, opts: ProxyOptions) -> CumulocityClient:
    """Create Cumulocity client and prompt for missing credentials
    if necessary.

    Args:
        ctx (click.Context): Click context
        opts (ProxyOptions): Proxy options

    Returns:
        CumulocityClient: Configured Cumulocity client
    """
    client = CumulocityClient(
        hostname=opts.host,
        tenant=opts.tenant,
        user=opts.user,
        password=opts.password,
        tfacode=opts.tfa_code,
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


def get_config_id(mor: Dict[str, Any], config: str) -> str:
    """Get the remote access configuration id matching a specific type
    from a device managed object

    Args:
        mor (Dict[str, Any]): Device managed object
        config (str): Expected configuration type

    Returns:
        str: Remote access configuration id
    """
    if "c8y_RemoteAccessList" not in mor:
        device = mor["name"]
        logging.error(
            'No Remote Access Configuration has been found for device "%s"', device
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
                'Using Configuration with Name "%s" and Remote Port %s',
                config,
                remote_access["port"],
            )
            break
        if not config:
            config_id = remote_access["id"]
            logging.info(
                'Using Configuration with Name "%s" and Remote Port %s',
                config,
                remote_access["port"],
            )
            break
    if not config_id:
        if config:
            logging.error(
                'Provided config name "%s" for "%s" was not found or none with protocal set to "PASSTHROUGH"',
                config,
                device,
            )
            sys.exit(1)
        else:
            logging.error(
                'No config with protocal set to "PASSTHROUGH" has been found for device "%s"',
                device,
            )
            sys.exit(1)
    return config_id


def start_proxy(ctx: click.Context, opts: ProxyOptions) -> NoReturn:
    """Start the local proxy

    Args:
        ctx (click.Context): Click context
        opts (ProxyOptions): Proxy options
    """
    # pylint: disable=too-many-branches,too-many-statements
    if platform.system() in ("Linux", "Darwin"):
        signal.signal(signal.SIGUSR1, signal_handler)
    else:
        signal.signal(signal.SIGINT, signal_handler)

    configure_logger(verbose=opts.verbose)

    if opts.use_pid:
        try:
            upsert_pid_file(
                opts.pidfile, opts.device, opts.host, opts.config, opts.user
            )
        except PermissionError:
            ctx.exit(ExitCodes.PID_FILE_ERROR)
    if opts.kill:
        if opts.use_pid:
            kill_existing_instances(opts.pidfile)
        else:
            logging.warning(
                'Killing existing instances is only supported when "--use-pid" is used.'
            )

    try:
        client = create_client(ctx, opts)
        mor = client.get_managed_object(opts.device, opts.external_type)
        config_id = get_config_id(mor, opts.config)
        device_id = mor.get("id")

        is_authorized = client.validate_remote_access_role()
        if not is_authorized:
            logging.error(
                "User %s is not authorized to use Cloud Remote Access. Contact your Cumulocity Admin!",
                opts.user,
            )
            ctx.exit(ExitCodes.NOT_AUTHORIZED)
    except Exception as ex:
        logging.error("Could not retrieve device information. reason=%s", ex)
        ctx.exit(ExitCodes.UNKNOWN)

    client_opts = {
        "host": opts.host,
        "config_id": config_id,
        "device_id": device_id,
        "session": client.session,
        "token": opts.token,
        "ignore_ssl_validate": opts.ignore_ssl_validate,
        "ping_interval": opts.ping_interval,
    }

    try:
        tcp_server = TCPProxyServer(
            opts.port,
            WebsocketClient(**client_opts),
            opts.tcp_size,
            opts.tcp_timeout,
            opts.scriptmode,
            max_reconnects=opts.reconnects,
        )

        exit_code = ExitCodes.OK

        click.secho(BANNER1)
        logging.info("Starting tcp server")

        background = threading.Thread(target=tcp_server.serve_forever, daemon=True)
        background.start()

        if not tcp_server.wait_for_running(30.0):
            logging.warning(
                "Server did not start up in time, but trying to proceed anyway"
            )

        if opts.execute_script:
            logging.info("Executing script")
            exit_code = run_script(ctx, opts)
            raise ExitCommand()

        if opts.ssh_user:
            exit_code = start_ssh(ctx, opts)
            raise ExitCommand()

        click.secho(
            f"\nc8ylp is listening for device (ext_id) {opts.device} on localhost:{opts.port}",
            fg="green",
        )
        ssh_username = opts.ssh_user or "<username>"
        click.secho(
            f"\nConnect to {opts.device} by executing the following in a new tab/console:\n\n"
            f"\tssh -p {opts.port} {ssh_username}@localhost",
            color=True,
        )

        # loop, waiting for server to stop
        while background.is_alive():
            time.sleep(1)
            logging.debug(
                "Waiting in background: alive=%s",
                background.is_alive(),
            )
    except ExitCommand:
        pass
    except Exception as ex:
        if str(ex):
            logging.error("Error on TCP-Server. %s", ex)
            exit_code = ExitCodes.UNKNOWN
    finally:
        if opts.use_pid:
            clean_pid_file(opts.pidfile, os.getpid())

        tcp_server.shutdown()
        background.join()
        logging.info("Exit code: %s", exit_code)
        click.echo("Exiting")
        ctx.exit(exit_code)


def upsert_pid_file(pidfile: str, device: str, url: str, config: str, user: str):
    """Create/update pid file

    Args:
        pidfile (str): PID file path
        device (str): Device external identity
        url (str): Cumulocity URL
        config (str): Remote access configuration type
        user (str): Cumulocity user
    """
    try:
        clean_pid_file(pidfile, os.getpid())
        pid_file_text = get_pid_file_text(device, url, config, user)
        logging.debug("Adding %s to PID-File %s", pid_file_text, pidfile)

        if not os.path.exists(pidfile):
            if not os.path.exists(os.path.dirname(pidfile)):
                os.makedirs(os.path.dirname(pidfile))

        with open(pid_file_text, "a+") as file:
            file.seek(0)
            file.write(pid_file_text)
            file.write("\n")

    except PermissionError:
        logging.error(
            "Could not write PID-File %s. Please create the folder manually and assign the correct permissions.",
            pidfile,
        )
        raise


def run_script(_ctx: click.Context, opts: ProxyOptions) -> int:
    """Execute a script with environment variables set with information
    about the local proxy, i.e. device, port etc.

    Args:
        ctx (click.Context): Click context
        opts (ProxyOptions): Proxy options

    Returns:
        int: Exit code of script
    """

    cmd_args = [
        opts.execute_script,
    ]

    if opts.script_args:
        cmd_args.extend(opts.script_args)

    env = {
        **os.environ,
        "PORT": str(opts.port),
        "DEVICE": str(opts.device),
        "DEVICE_USER": str(opts.ssh_user),
    }

    logging.info("Executing extension: %s", " ".join(cmd_args))
    exit_code = subprocess.call(cmd_args, env=env, shell=False)
    if exit_code != 0:
        logging.warning("Script exited with a non-zero exit code. code=%s", exit_code)

    return exit_code


def start_ssh(_ctx: click.Context, opts: ProxyOptions) -> int:
    """Start interactive ssh session

    Args:
        ctx (click.Context): Click context
        opts (ProxyOptions): Proxy options

    Returns:
        int: Exit code of ssh command
    """
    if not shutil.which("ssh"):
        raise Exception(
            "ssh client not found. Please make sure the 'ssh' client is included in your PATH variable"
        )

    ssh_args = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-p",
        str(opts.port),
        f"{opts.ssh_user}@localhost",
    ]

    if opts.ssh_command:
        logging.info("Executing a once-off command then exiting")
        ssh_args.extend([opts.ssh_command])
        click.secho(f"Executing command via ssh on {opts.device}", fg="green")
    else:
        click.secho(
            f"Starting interactive ssh session with {opts.device} ({opts.host})",
            fg="green",
        )

    logging.info("Starting ssh session using: %s", " ".join(ssh_args))
    session_start = time.monotonic()
    exit_code = subprocess.call(ssh_args, env=os.environ)
    session_duration = timedelta(seconds=(int(time.monotonic() - session_start)))
    if exit_code != 0:
        logging.warning("SSH exited with a non-zero exit code. code=%s", exit_code)

    msg = f"SSH Session duration: {session_duration}"
    logging.info(msg)
    click.echo(msg)
    return exit_code


def get_pid_file_text(device: str, url: str, config: str, user: str) -> str:
    """Format pid file text contents

    Args:
        device (str): Device external identity
        url (str): Cumulocity url
        config (str): Remote access type
        user (str): User

    Returns:
        str: Text contents that should be written to a pid file
    """
    pid = str(os.getpid())
    return f"{pid},{url},{device},{config},{user}"


def get_pid_from_line(line: str) -> int:
    """Get the process id from the contents of a pid file

    Args:
        line (str): Encoded PID information

    Returns:
        int: Porcess id
    """
    return int(str.split(line, ",")[0])


def pid_is_active(pid: int) -> bool:
    """Check if a PID is active

    Args:
        pid (int): Process ID

    Returns:
        bool: True if the process is still running
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def clean_pid_file(pidfile: str, pid: int):
    """Clean up pid file

    Args:
        pidfile (str): PID file path
        pid (int): current process id
    """
    if os.path.exists(pidfile):
        logging.debug("Cleaning Up PID %s in PID-File %s", pid, pidfile)
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


def kill_existing_instances(pidfile: str):
    """Kill existing instances of c8ylp

    Args:
        pidfile (str): PID file path
    """
    if os.path.exists(pidfile):
        with open(pidfile) as file:
            pid = int(os.getpid())
            for line in file:
                other_pid = get_pid_from_line(line)
                if pid != other_pid and pid_is_active(other_pid):
                    logging.info("Killing other running Process with PID %s", other_pid)
                    os.kill(get_pid_from_line(line), 9)
                clean_pid_file(pidfile, other_pid)


if __name__ == "__main__":
    # --pylint: disable=no-value-for-parameter
    cli()
