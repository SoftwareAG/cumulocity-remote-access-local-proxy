"""version command"""

import click

from .. import __version__
from .core import ExitCodes


@click.command()
@click.pass_context
def version(ctx: click.Context):
    """Show the c8ylp version number"""
    click.echo(f"Version {__version__}")
    ctx.exit(ExitCodes.OK)
