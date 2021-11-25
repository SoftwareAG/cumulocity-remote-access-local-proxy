"""server command"""

import click

from .. import options
from .core import ProxyContext


@click.command()
@options.common_options
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
        c8ylp server device01 --host https://example.c8y.io

    Example 2: Start the local proxy using environment file

        \b
        c8ylp server --env-file .env device01

    Example 3: Start the local proxy with randomized port

        \b
        c8ylp server --env-file .env --port 0 device01
    """
    proxy = ProxyContext(ctx, kwargs)
    proxy.start()
