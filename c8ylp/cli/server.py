"""server command"""

import click

from .. import options
from .core import ProxyOptions, start_proxy


@click.command()
@options.ARG_DEVICE
@options.common_options
@options.KILL_EXISTING
@options.PID_USE
@options.PID_FILE
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
