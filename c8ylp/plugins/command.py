"""plugin: command. Used to execute a user defined command or script"""

import logging
import os
import subprocess
from typing import List

import click
from c8ylp import options

from c8ylp.cli.core import ProxyContext


@click.command()
@options.common_options
@click.argument(
    "additional_args",
    metavar="[REMOTE_COMMANDS]...",
    nargs=-1,
    type=click.UNPROCESSED,
)
@click.pass_context
def cli(ctx: click.Context, additional_args: List[str], **kwargs):
    """
    Start once-off proxy and execute a (local) script/command

        \b
        DEVICE is the device's external identity
        SCRIPT is the script or command to run after the proxy has been started

        All additional arguments will be passed to the script/command. Use "--" before
        the additional arguments to prevent the arguments from being interpreted by
        c8ylp (i.e. to avoid clashes with c8ylp).

    \b
    Available ENV variables (use single quotes to prevent expansion):

      \b
      DEVICE - external device identity
      PORT   - port number of the local proxy

    \b
    Example 1: Use scp to copy a file to a device

        \b
        c8ylp plugin command --env-file .env device01 \\
            -- /usr/bin/scp -P '$PORT' myfile.tar.gz admin@localhost:/tmp

    Example 2: Run a custom script (not included) to copy a file from the device to
    the current folder

        \b
        c8ylp plugin command --env-file .env -v device01 ./copyfrom.sh /var/log/dpkg.log ./
    """

    cmd_args = []

    if not additional_args:
        raise click.BadParameter(
            "At least one command as a positional argument needs to be provided"
        )

    proxy = ProxyContext(ctx, kwargs).start_background()

    if additional_args:
        for value in additional_args:
            expanded_value = os.path.expandvars(value)
            logging.info("Expanded script arguments: %s => %s", value, expanded_value)
            cmd_args.append(expanded_value)

    proxy.show_message(f"Running custom command: {' '.join(cmd_args)}")

    exit_code = subprocess.call(cmd_args, env=os.environ, shell=False)
    if exit_code != 0:
        proxy.show_error(f"Command exited with a non-zero exit code. code={exit_code}")
    ctx.exit(exit_code)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
