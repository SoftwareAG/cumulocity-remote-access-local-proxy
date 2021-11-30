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
"""Exit codes"""

import dataclasses
import logging
import os
import pathlib
import signal
import threading
import time
import sys
from enum import IntEnum
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, NoReturn, Optional

import click

from ..timer import CommandTimer
from ..banner import BANNER1
from ..env import save_env
from ..rest_client.c8yclient import CumulocityClient, CumulocityMissingTFAToken
from ..tcp_socket import TCPProxyServer
from ..websocket_client import WebsocketClient


class ExitCodes(IntEnum):
    """Exit codes"""

    OK = 0
    NO_SESSION = 2
    NOT_AUTHORIZED = 3

    DEVICE_MISSING_REMOTE_ACCESS_FRAGMENT = 5
    DEVICE_NO_PASSTHROUGH_CONFIG = 6
    DEVICE_NO_MATCHING_PASSTHROUGH_CONFIG = 7
    MISSING_ROLE_REMOTE_ACCESS_ADMIN = 8

    UNKNOWN = 9

    SSH_NOT_FOUND = 10
    TIMEOUT_WAIT_FOR_PORT = 11
    COMMAND_NOT_FOUND = 12
    PLUGIN_EXECUTION_ERROR = 20
    PLUGIN_INVALID_FORMAT = 21
    PLUGIN_NOT_FOUND = 22
    TERMINATE = 100


@dataclasses.dataclass
class ProxyContext:
    """Local proxy context"""

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
    ping_interval = 0
    kill = False
    tcp_size = 0
    tcp_timeout = 0
    verbose = False
    ignore_ssl_validate = False
    reconnects = 0
    ssh_user = ""
    additional_args = None
    disable_prompts = False
    env_file = None
    store_token = False
    wait_port_timeout = 60.0

    def __init__(self, ctx: click.Context, src_dict: Dict[str, Any] = None) -> None:
        self._ctx = ctx
        if src_dict is not None:
            self.fromdict(src_dict)

            configure_logger(CliLogger.log_path(), self.verbose)

    @property
    def _root_context(self) -> click.Context:
        return self._ctx.find_root().ensure_object(dict)

    @property
    def used_port(self) -> int:
        """Get the port used by the local proxy

        Returns:
            int: Port number
        """
        return self._root_context.get("used_port", self.port)

    @used_port.setter
    def used_port(self, value: int):
        """Store the port used by the local proxy for later reference

        Args:
            value (int): Port number
        """
        self._root_context["used_port"] = value

    def exit_server_not_ready(self) -> NoReturn:
        """Exit with a server not ready error

        Returns:
            NoReturn: The function does not return
        """
        self.show_error(
            "Timed out waiting for local port to open: "
            f"port={self.used_port}, timeout={self.wait_port_timeout}s"
        )
        self._ctx.exit(ExitCodes.TIMEOUT_WAIT_FOR_PORT)

    def fromdict(self, src_dict: Dict[str, Any]) -> "ProxyContext":
        """Load proxy settings from a dictionary

        Args:
            src_dict (Dict[str, Any]): [description]

        Returns:
            ProxyContext: Proxy options after the values have been set
                via the dictionary
        """
        logging.info("Loading from dictionary")
        assert isinstance(src_dict, dict)
        for key, value in src_dict.items():
            logging.info("reading key: %s=%s", key, value)
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def start_background(self, ctx: click.Context = None) -> "ProxyContext":
        """Start the local proxy in the background

        Returns:
            ProxyContext: Reference to the proxy context so it can be chained
                with other commands or used after the initialization of the class.
        """
        cur_ctx = ctx or self._ctx
        connection_data = pre_start_checks(cur_ctx, self)
        ready_signal = threading.Event()
        run_proxy_in_background(
            cur_ctx, self, connection_data=connection_data, ready_signal=ready_signal
        )
        if not ready_signal.wait(self.wait_port_timeout):
            self.exit_server_not_ready()
        return self

    def start(self, ctx: click.Context = None) -> None:
        """Start the local proxy in the background

        Returns:
            ProxyContext: Reference to the proxy context so it can be chained
                with other commands or used after the initialization of the class.
        """
        cur_ctx = ctx or self._ctx
        connection_data = pre_start_checks(cur_ctx, self)
        start_proxy(cur_ctx, self, connection_data=connection_data)

    @classmethod
    def show_message(cls, msg: str, *args, **kwargs):
        """Show an message to the user and log it

        Args:
            msg (str): User message to print on the console
        """
        click.secho(msg, fg="green")
        logging.info(msg, *args, **kwargs)

    def show_error(self, msg: str, *args, **kwargs):
        """Show an error to the user and log it

        Args:
            msg (str): User message to print on the console
        """
        if not self.verbose:
            click.secho(msg, fg="red")

        logging.warning(msg, *args, **kwargs)

    def show_info(self, msg: str, *args, **kwargs):
        """Show an info message to the user and log it

        Args:
            msg (str): User message to print on the console
        """
        if not self.verbose:
            click.secho(msg)

        logging.warning(msg, *args, **kwargs)

    def show_warning(self, msg: str, *args, **kwargs):
        """Show a warning to the user and log it

        Args:
            msg (str): User message to print on the console
        """
        if not self.verbose:
            click.secho(msg, fg="yellow")

        logging.warning(msg, *args, **kwargs)

    def set_env(self):
        """Set environment variables so information about the proxy can
        be access by plugins
        """
        os.environ["C8Y_HOST"] = str(self.host)
        os.environ["PORT"] = str(self.used_port)
        os.environ["DEVICE"] = self.device

        # Support WSL environments and expose variables to be explosed to WSL
        os.environ["WSLENV"] = "PORT/u:DEVICE/u:C8Y_HOST/u"


@dataclasses.dataclass
class RemoteAccessConnectionData:
    """Remote access connection data"""

    client: CumulocityClient
    managed_object_id: str
    remote_config_id: str


PASSTHROUGH = "PASSTHROUGH"
REMOTE_ACCESS_FRAGMENT = "c8y_RemoteAccessList"


class CliLogger:
    """CLI Logger"""

    # pylint: disable=too-few-public-methods

    @classmethod
    def log_path(cls) -> pathlib.Path:
        """Get the log path"""
        return (
            pathlib.Path(os.getenv("C8YLP_LOG_DIR", "~/.c8ylp/")).expanduser()
            / "localproxy.log"
        )


def configure_logger(path: pathlib.Path, verbose: bool = False) -> logging.Logger:
    """Configure logger

    Args:
        path (pathlib.Path): Path where the persistent logger should write to.
        verbose (bool, optional): Use verbose logging. Defaults to False.

    Returns:
        logging.Logger: Created logger
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    log_file_formatter = logging.Formatter(
        "%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s"
    )

    # Set default log format
    if verbose:
        log_console_formatter = logging.Formatter(
            "[c8ylp]  %(levelname)-5s %(message)s"
        )
        console_loglevel = logging.INFO
        if len(logger.handlers) == 0:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_console_formatter)
            console_handler.setLevel(console_loglevel)
            logger.addHandler(console_handler)
        else:
            handler = logger.handlers[0]
            # ignore console log messages
            handler.setLevel(console_loglevel)
            handler.setFormatter(log_console_formatter)
    else:
        # Remove default console logging and only use file logging
        logger.handlers = []

    # Max 5 log files each 10 MB.
    rotate_handler = RotatingFileHandler(
        filename=str(path), maxBytes=10000000, backupCount=5
    )
    rotate_handler.setFormatter(log_file_formatter)
    rotate_handler.setLevel(logging.INFO)

    # Log to Rotating File
    logger.addHandler(rotate_handler)
    return logger


def signal_handler(_signal, _frame):
    """Signal handler"""
    sys.exit(ExitCodes.TERMINATE)


def register_signals():
    """Register signal handlers"""
    signal.signal(signal.SIGINT, signal_handler)


def create_client(ctx: click.Context, opts: ProxyContext) -> CumulocityClient:
    """Create Cumulocity client and prompt for missing credentials
    if necessary.

    Args:
        ctx (click.Context): Click context
        opts (ProxyContext): Proxy options

    Returns:
        CumulocityClient: Configured Cumulocity client
    """
    if not opts.disable_prompts and not opts.host:
        opts.host = click.prompt(
            text="Enter the Cumulocity Host/URL",
        )

    client = CumulocityClient(
        hostname=opts.host,
        tenant=opts.tenant,
        user=opts.user,
        password=opts.password,
        tfacode=opts.tfa_code,
        token=opts.token,
        ignore_ssl_validate=opts.ignore_ssl_validate,
    )

    if not client.url:
        opts.show_error(
            "No Cumulocity host was provided. The host can be set via"
            "environment variables, arguments or the env-file"
        )
        ctx.exit(ExitCodes.NO_SESSION)

    logging.info("Checking tenant id")
    client.validate_tenant_id()

    # Retry logging so the user can be prompted for
    # their credentials/TFA code etc. without having to run c8ylp again
    retries = 3
    success = False
    while retries:
        try:
            if client.token:
                client.validate_credentials()
            else:
                client.login()

            if opts.env_file and opts.store_token:
                store_credentials(opts, client)

            success = True
            break
        except CumulocityMissingTFAToken as ex:
            client.tfacode = click.prompt(
                text="Enter your Cumulocity TFA-Token", hide_input=False
            )
        except Exception as ex:
            logging.info("unknown exception: %s", ex)

            if not opts.disable_prompts:
                if not client.user:
                    client.user = click.prompt(
                        text="Enter your Cumulocity Username",
                    )

                if not client.password:
                    client.password = click.prompt(
                        text="Enter your Cumulocity Password [input hidden]",
                        hide_input=True,
                    )

        retries -= 1

    if not success:
        logging.info("Could not create client")
        ctx.exit(ExitCodes.NO_SESSION)

    return client


def store_credentials(opts: ProxyContext, client: CumulocityClient):
    """Store credentials to the environment file. It creates
    the file if it does not already exist.

    The file will only be written to if it has changed.

    Args:
        opts (ProxyContext): Proxy options
        client (CumulocityClient): Cumulocity client containing valid
            credentials
    """
    changed = save_env(
        opts.env_file,
        {
            # Note: Don't save password!
            "C8Y_HOST": client.url,
            "C8Y_USER": client.user,
            "C8Y_TENANT": client.tenant,
            "C8Y_TOKEN": client.token,
        },
    )

    if changed:
        opts.show_message(f"Env file was updated: {opts.env_file}")
    else:
        opts.show_info(f"Env file is already up to date: {opts.env_file}")


def get_config_id(ctx: click.Context, mor: Dict[str, Any], config: str) -> str:
    """Get the remote access configuration id matching a specific type
    from a device managed object

    Args:
        mor (Dict[str, Any]): Device managed object
        config (str): Expected configuration type

    Returns:
        str: Remote access configuration id
    """
    device_name = mor.get("name", "<<empty_name>>")
    if REMOTE_ACCESS_FRAGMENT not in mor:
        logging.error(
            'No Remote Access Configuration has been found for device "%s"', device_name
        )
        ctx.exit(ExitCodes.DEVICE_MISSING_REMOTE_ACCESS_FRAGMENT)

    valid_configs = [
        item
        for item in mor.get(REMOTE_ACCESS_FRAGMENT, [])
        if item.get("protocol") == PASSTHROUGH
    ]

    if not valid_configs:
        logging.error(
            'No config with protocol set to "%s" has been found for device "%s"',
            PASSTHROUGH,
            device_name,
        )
        ctx.exit(ExitCodes.DEVICE_NO_PASSTHROUGH_CONFIG)

    def extract_config_id(matching_config):
        logging.info(
            'Using Configuration with Name "%s" and Remote Port %s',
            matching_config.get("name"),
            matching_config.get("port"),
        )
        return matching_config.get("id")

    if not config:
        # use first config
        return extract_config_id(valid_configs[0])

    # find config matching name
    matches = [
        item
        for item in valid_configs
        if item.get("name", "").casefold() == config.casefold()
    ]

    if not matches:
        logging.error(
            'Provided config name "%s" for "%s" was not found or none with protocal set to "%s"',
            config,
            device_name,
            PASSTHROUGH,
        )
        ctx.exit(ExitCodes.DEVICE_NO_MATCHING_PASSTHROUGH_CONFIG)

    return extract_config_id(matches[0])


def run_proxy_in_background(
    ctx: click.Context,
    opts: ProxyContext,
    connection_data: RemoteAccessConnectionData,
    ready_signal: threading.Event = None,
):
    """Run the proxy in a background thread

    Args:
        ctx (click.Context): Click context
        opts (ProxyContext): Proxy options
        connection_data (RemoteAccessConnectionData): Remote access connection data
    """

    stop_signal = threading.Event()
    _local_ready_signal = threading.Event()

    # register signals as the proxy will be starting in a background thread
    # to enable the proxy to run as a subcommand
    register_signals()

    # Start the proxy in a background thread so the user can
    background = threading.Thread(
        target=start_proxy,
        args=(ctx, opts),
        kwargs=dict(
            connection_data=connection_data,
            stop_signal=stop_signal,
            ready_signal=_local_ready_signal,
        ),
        daemon=True,
    )
    background.start()

    # Block until the local proxy is ready to accept connections
    if not _local_ready_signal.wait(opts.wait_port_timeout):
        opts.exit_server_not_ready()

    # Inject custom env variables for use within the script
    opts.set_env()

    # The subcommand is called after this
    timer = CommandTimer("Duration", on_exit=click.echo).start()

    # Shutdown the server once the plugin has been run
    @ctx.call_on_close
    def _shutdown_server_thread():
        stop_signal.set()
        background.join()
        timer.stop_with_message()

    # Only set ready signal once the whole env include env variables has
    # been setup
    if ready_signal:
        ready_signal.set()


def pre_start_checks(
    ctx: click.Context, opts: ProxyContext
) -> Optional[RemoteAccessConnectionData]:
    """Run prestart checks before starting the local proxy

    Args:
        ctx (click.Context): Click context
        opts (ProxyContext): Proxy options

    Returns:
        Optional[RemoteAccessConnectionData]: Remote access connection data
    """

    try:
        client = create_client(ctx, opts)
        mor = client.get_managed_object(opts.device, opts.external_type)
        config_id = get_config_id(ctx, mor, opts.config)
        device_id = mor.get("id")

        is_authorized = client.validate_remote_access_role()
        if not is_authorized:
            opts.show_error(
                "The user is not authorized to use Cloud Remote Access. "
                f"Contact your Cumulocity Admin. user={opts.user}",
            )
            ctx.exit(ExitCodes.MISSING_ROLE_REMOTE_ACCESS_ADMIN)

    except Exception as ex:
        if isinstance(ex, click.exceptions.Exit):
            opts.show_error(f"Could not retrieve device information. reason={ex}")
            # re-raise existing exit
            raise

        error_context = ""
        extra_details = []
        if opts.host and opts.host not in str(ex):
            extra_details.append(f"host={opts.host or ''}")

        if opts.user and opts.user not in str(ex):
            extra_details.append(f"user={opts.user or ''}")

        if extra_details:
            error_context = ". settings: " + ", ".join(extra_details)

        opts.show_error(
            "Unexpected error when retrieving device information from Cumulocity. "
            f"error_details={ex}{error_context}"
        )
        ctx.exit(ExitCodes.NOT_AUTHORIZED)

    return RemoteAccessConnectionData(
        client=client, managed_object_id=device_id, remote_config_id=config_id
    )


def start_proxy(
    ctx: click.Context,
    opts: ProxyContext,
    connection_data: RemoteAccessConnectionData,
    stop_signal: threading.Event = None,
    ready_signal: threading.Event = None,
) -> NoReturn:
    """Start the local proxy

    Args:
        ctx (click.Context): Click context
        opts (ProxyContext): Proxy options
    """
    # pylint: disable=too-many-branches,too-many-statements
    is_main_thread = threading.current_thread() is threading.main_thread()
    if is_main_thread:
        register_signals()

    client_opts = {
        "host": opts.host,
        "config_id": connection_data.remote_config_id,
        "device_id": connection_data.managed_object_id,
        "session": connection_data.client.session,
        "token": opts.token,
        "ignore_ssl_validate": opts.ignore_ssl_validate,
        "ping_interval": opts.ping_interval,
        "max_retries": 2,
    }

    tcp_server = None
    background = None

    try:
        tcp_server = TCPProxyServer(
            opts.port,
            WebsocketClient(**client_opts),
            opts.tcp_size,
            opts.tcp_timeout,
        )

        exit_code = ExitCodes.OK

        click.secho(BANNER1)
        logging.info("Starting tcp server")

        background = threading.Thread(target=tcp_server.serve_forever, daemon=True)
        background.start()

        # Block until the local proxy is ready to accept connections
        if not tcp_server.wait_for_running(opts.wait_port_timeout):
            opts.exit_server_not_ready()

        # store the used port for reference to later
        if tcp_server.server.socket:
            opts.used_port = tcp_server.server.socket.getsockname()[1]

        # Plugins start in a background thread so don't display it
        # as the plugins should do their own thing
        if is_main_thread:
            opts.show_info(
                f"\nc8ylp is listening for device (ext_id) {opts.device} ({opts.host}) on localhost:{opts.used_port}",
            )
            ssh_username = opts.ssh_user or "<device_username>"
            opts.show_message(
                f"\nFor example, if you are running a ssh proxy, you connect to {opts.device} by executing the "
                "following in a new tab/console:\n\n"
                f"\tssh -p {opts.used_port} {ssh_username}@localhost",
            )

            opts.show_info("\nPress ctrl-c to shutdown the server")

        if ready_signal:
            ready_signal.set()

        # loop, waiting for server to stop
        while background.is_alive():
            if stop_signal and stop_signal.is_set():
                break
            time.sleep(1)
            logging.debug(
                "Waiting in background: alive=%s",
                background.is_alive(),
            )
    except Exception as ex:
        if isinstance(ex, click.exceptions.Exit):
            # propagate exit code
            exit_code = getattr(ex, "exit_code")
            raise

        if str(ex):
            opts.show_error(
                "The local proxy TCP Server experienced an unexpected error. "
                f"port={opts.port}, error={ex}"
            )
            exit_code = ExitCodes.UNKNOWN
    finally:
        if tcp_server:
            tcp_server.shutdown()

        if background:
            background.join()

        if is_main_thread:
            if int(exit_code) == 0:
                opts.show_message(f"Exiting: {str(exit_code)} ({int(exit_code)})")
            else:
                opts.show_error(f"Exiting: {str(exit_code)} ({int(exit_code)})")

            ctx.exit(exit_code)
        else:
            opts.show_info("Exiting")
