"""Exit codes"""

import dataclasses
import logging
import os
import pathlib
import platform
import signal
import threading
import time
from enum import IntEnum
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, NoReturn, Optional

import click

from .. import pid
from ..helper import wait_for_port
from ..timer import CommandTimer
from ..banner import BANNER1
from ..env import save_env
from ..rest_client.c8yclient import CumulocityClient
from ..tcp_socket import TCPProxyServer
from ..websocket_client import WebsocketClient


class ExitCommand(Exception):
    """ExitCommand error"""


class ExitCodes(IntEnum):
    """Exit codes"""

    OK = 0
    NO_SESSION = 2
    NOT_AUTHORIZED = 3
    PID_FILE_ERROR = 4

    DEVICE_MISSING_REMOTE_ACCESS_FRAGMENT = 5
    DEVICE_NO_PASSTHROUGH_CONFIG = 6
    DEVICE_NO_MATCHING_PASSTHROUGH_CONFIG = 7
    MISSING_ROLE_REMOTE_ACCESS_ADMIN = 8

    UNKNOWN = 9

    SSH_NOT_FOUND = 10


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
    script_mode = False
    ignore_ssl_validate = False
    use_pid = False
    pid_file = ""
    reconnects = 0
    ssh_user = ""
    additional_args = None
    disable_prompts = False
    env_file = None
    store_token = False
    skip_exit = None

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


@dataclasses.dataclass
class RemoteAccessConnectionData:
    """Remote access connection data"""

    client: CumulocityClient
    managed_object_id: str
    remote_config_id: str


PASSTHROUGH = "PASSTHROUGH"
REMOTE_ACCESS_FRAGMENT = "c8y_RemoteAccessList"


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


def signal_handler(_signal, _frame):
    """Signal handler"""
    raise ExitCommand()


def register_signals():
    """Register signal handlers"""
    if platform.system() in ("Linux", "Darwin"):
        signal.signal(signal.SIGUSR1, signal_handler)
    else:
        signal.signal(signal.SIGINT, signal_handler)


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
    logging.info("Checking tenant id")
    client.validate_tenant_id()

    retries = 2
    success = False
    while retries:
        try:
            if client.token:
                client.validate_credentials()
            else:
                client.login_oauth()

            if opts.env_file and opts.store_token:
                store_credentials(opts, client)

            success = True
            break
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

                if not client.tfacode:
                    client.tfacode = click.prompt(
                        text="Enter your Cumulocity TFA-Token", hide_input=False
                    )
        retries -= 1

    if not success:
        logging.info("Could not create client")
        ctx.exit(ExitCodes.NO_SESSION)

    return client


def store_credentials(opts: ProxyOptions, client: CumulocityClient):
    """Store credentials to the environment file. It creates
    the file if it does not already exist.

    The file will only be written to if it has changed.

    Args:
        opts (ProxyOptions): Proxy options
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
        click.echo(f"Env file {opts.env_file} was updated")
    else:
        logging.info("Env file %s is already up to date", opts.env_file)


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
    ctx: click.Context, opts: ProxyOptions, connection_data: RemoteAccessConnectionData
):
    """Run the proxy in a background thread

    Args:
        ctx (click.Context): Click context
        opts (ProxyOptions): Proxy options
        connection_data (RemoteAccessConnectionData): Remote access connection data
    """

    stop_signal = threading.Event()
    opts.skip_exit = True

    # Inject custom env variables for use within the script
    os.environ["C8Y_HOST"] = str(opts.host)
    os.environ["PORT"] = str(opts.port)
    os.environ["DEVICE"] = str(opts.device)

    # register signals as the proxy will be starting in a background thread
    # to enable the proxy to run as a subcommand
    register_signals()

    # Start the proxy in a background thread so the user can
    background = threading.Thread(
        target=start_proxy,
        args=(ctx, opts),
        kwargs=dict(connection_data=connection_data, stop_signal=stop_signal),
        daemon=True,
    )
    background.start()

    # Block until the port is actually open
    wait_for_port(opts.port)

    # The subcommand is called after this
    timer = CommandTimer("Duration", on_exit=click.echo).start()

    # Shutdown the server once the plugin has been run
    @ctx.call_on_close
    def _shutdown_server_thread():
        stop_signal.set()
        background.join()
        timer.stop_with_message()


def pre_start_checks(
    ctx: click.Context, opts: ProxyOptions
) -> Optional[RemoteAccessConnectionData]:
    """Run prestart checks before starting the local proxy

    Args:
        ctx (click.Context): Click context
        opts (ProxyOptions): Proxy options

    Returns:
        Optional[RemoteAccessConnectionData]: Remote access connection data
    """
    configure_logger(verbose=opts.verbose)

    if opts.use_pid:
        try:
            pid.upsert_pid_file(
                opts.pid_file, opts.device, opts.host, opts.config, opts.user
            )
        except PermissionError:
            ctx.exit(ExitCodes.PID_FILE_ERROR)
    if opts.kill:
        if opts.use_pid:
            pid.kill_existing_instances(opts.pid_file)
        else:
            logging.warning(
                'Killing existing instances is only supported when "--use-pid" is used.'
            )

    try:
        client = create_client(ctx, opts)
        mor = client.get_managed_object(opts.device, opts.external_type)
        config_id = get_config_id(ctx, mor, opts.config)
        device_id = mor.get("id")

        is_authorized = client.validate_remote_access_role()
        if not is_authorized:
            logging.error(
                "User %s is not authorized to use Cloud Remote Access. Contact your Cumulocity Admin!",
                opts.user,
            )
            ctx.exit(ExitCodes.MISSING_ROLE_REMOTE_ACCESS_ADMIN)

    except Exception as ex:
        if isinstance(ex, click.exceptions.Exit):
            logging.error("Could not retrieve device information. reason=%s", ex)
            # re-raise existing exit
            raise
        ctx.exit(ExitCodes.NOT_AUTHORIZED)

    return RemoteAccessConnectionData(
        client=client, managed_object_id=device_id, remote_config_id=config_id
    )


def start_proxy(
    ctx: click.Context,
    opts: ProxyOptions,
    connection_data: RemoteAccessConnectionData,
    stop_signal: threading.Event = None,
) -> NoReturn:
    """Start the local proxy

    Args:
        ctx (click.Context): Click context
        opts (ProxyOptions): Proxy options
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
    }

    tcp_server = None

    try:
        tcp_server = TCPProxyServer(
            opts.port,
            WebsocketClient(**client_opts),
            opts.tcp_size,
            opts.tcp_timeout,
            opts.script_mode,
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

        # Plugins start in a background thread so don't display it
        # as the plugins should do their own thing
        if is_main_thread:
            click.secho(
                f"\nc8ylp is listening for device (ext_id) {opts.device} ({opts.host}) on localhost:{opts.port}",
                fg="green",
            )
            ssh_username = opts.ssh_user or "<device_username>"
            click.secho(
                f"\nConnect to {opts.device} by executing the following in a new tab/console:\n\n"
                f"\tssh -p {opts.port} {ssh_username}@localhost",
                color=True,
            )

        # loop, waiting for server to stop
        while background.is_alive() and (stop_signal and not stop_signal.is_set()):
            time.sleep(1)
            logging.debug(
                "Waiting in background: alive=%s",
                background.is_alive(),
            )
    except ExitCommand:
        pass
    except Exception as ex:
        if isinstance(ex, click.exceptions.Exit):
            # propagate exit code
            exit_code = getattr(ex, "exit_code")
            raise

        if str(ex):
            logging.error("Error on TCP-Server. %s", ex)
            exit_code = ExitCodes.UNKNOWN
    finally:
        if opts.use_pid:
            pid.clean_pid_file(opts.pid_file, os.getpid())

        if tcp_server:
            tcp_server.shutdown()

        background.join()
        logging.info("Exit code: %s", exit_code)
        click.echo("Exiting")

        if is_main_thread:
            ctx.exit(exit_code)
