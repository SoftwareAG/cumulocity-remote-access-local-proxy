"""connect command group"""

import click

from .ssh import cli as ssh


@click.group(options_metavar="")
def connect():
    """Connect to a device via different protocols (i.e. via ssh)

    A local proxy instance is started automatically (defaults to a random port)
    and the a client of the selected protocol (i.e. ssh) is called to connect
    to it.

    The local proxy instance is shutdown after the client disconnects.
    """


connect.add_command(ssh, name="ssh")
