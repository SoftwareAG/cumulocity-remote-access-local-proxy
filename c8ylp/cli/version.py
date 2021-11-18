"""version command"""

from typing import Any

import click

from .. import __version__
from .core import ExitCodes


def print_version(ctx: click.Context, _param: click.Parameter, _value: Any) -> Any:
    """Print command version

    Args:
        ctx (click.Context): Click context
        _param (click.Parameter): Click param
        value (Any): Parameter value

    Returns:
        Any: Parameter value
    """
    click.echo(f"Version {__version__}")
    ctx.exit(ExitCodes.OK)


@click.command()
@click.pass_context
def version(ctx):
    """Show version number"""
    print_version(ctx, None, None)
