"""server command"""

import click

from .. import options
from .core import ProxyOptions, start_proxy


@click.command()
@options.ARG_DEVICE
@options.HOSTNAME
@options.EXTERNAL_IDENTITY_TYPE
@options.REMOTE_ACCESS_TYPE
@options.C8Y_TENANT
@options.C8Y_USER
@options.C8Y_TOKEN
@options.C8Y_PASSWORD
@options.C8Y_TFA_CODE
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
@options.DISABLE_PROMPT
@options.STORE_TOKEN
@click.pass_context
def server(
    ctx,
    *_args,
    **kwargs,
):
    """Start local proxy in server mode

    \b
        DEVICE is the device's external identity

    Once the local proxy has started, clients such as ssh and scp can be used
    to establish a connection to the device.

    \b
    Example 1: Start the local proxy, prompt for credentials (if not set via env variables)

        \b
        c8ylp start --host https://example.c8y.io device01

    Example 2: Start the local proxy using environment file

        \b
        c8ylp start --env-file .env device01

    Example 3: Start the local proxy with randomized port

        \b
        c8ylp start --env-file .env device01 --port 0
    """
    opts = ProxyOptions().fromdict(kwargs)
    start_proxy(ctx, opts)
