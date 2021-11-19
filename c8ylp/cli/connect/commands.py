"""connect command group"""
import sys

import click

from ... import options
from ..core import ProxyOptions, run_proxy_in_background
from .ssh import cli as ssh


@click.group()
@options.ARG_DEVICE
@options.common_options
@click.pass_context
def connect(ctx, *_args, **kwargs):
    """Connect actions"""
    click.echo("Running pre-install phase")
    opts = ProxyOptions().fromdict(kwargs)
    opts.script_mode = True

    # Skip starting server if the user just want to see the help
    if "--help" in sys.argv or "-h" in sys.argv:
        return
    run_proxy_in_background(ctx, opts)


connect.add_command(ssh, name="ssh")
