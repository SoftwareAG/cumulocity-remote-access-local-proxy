"""connect command group"""

import click

from .ssh import cli as ssh


@click.group(options_metavar="")
def connect():
    """Connect commands

    Connect to a device via SSH by starting a local proxy and then
    launching a ssh client
    """


connect.add_command(ssh, name="ssh")
