"""ssh. Used to start an interactive ssh session or execute a single ssh
command then exit.
"""

import logging
import os
import shutil
import subprocess
from typing import List

import click
from c8ylp.cli.core import ExitCodes


@click.command()
@click.option(
    "--ssh-user",
    required=True,
    prompt=True,
    help="SSH username which is configured on the device",
)
@click.argument(
    "additional_args", metavar="[REMOTE_COMMANDS]...", nargs=-1, type=click.UNPROCESSED
)
@click.pass_context
def cli(ctx: click.Context, ssh_user: str, additional_args: List[str]):
    """Start once-off proxy and connect via ssh

    An interactive ssh is opened if a remote command is not provided.

    Once the ssh session is closed, then the local proxy will be shutdown.

    Use "--" before the remote commands to prevent the arguments
    from being interpreted by c8ylp (i.e. to avoid clashes with c8ylp).

    \b
        DEVICE is the device's external identity

    Example 1: Start an interactive SSH connection

    \b
        c8ylp connect --env-file .env ssh device01 --ssh-user admin

    Example 2: Execute a command via SSH

    \b
        c8ylp connect --env-file .env ssh device01 --ssh-user admin -- systemctl status ssh

    Example 3: Execute a complex command via SSH (use quotes to ensure command is sent to the device)

    \b
        c8ylp plugin --env-file .env device01 ssh --ssh-user admin -- "systemctl status ssh; dpkg --list | grep ssh"

    """

    logging.info("Parent context: %s", ctx.parent.params)
    if not shutil.which("ssh"):
        logging.error(
            "ssh client not found. Please make sure the 'ssh' client is included in your PATH variable"
        )

        ctx.exit(ExitCodes.SSH_NOT_FOUND)

    port = os.getenv("PORT")
    device = os.getenv("DEVICE")
    host = os.getenv("C8Y_HOST")

    ssh_args = [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-p",
        port,
        f"{ssh_user}@localhost",
    ]

    if additional_args:
        logging.info("Executing a once-off command then exiting")
        ssh_args.extend(additional_args)
        click.secho(f"Executing command via ssh on {device} ({host})", fg="green")
    else:
        click.secho(
            f"Starting interactive ssh session with {device} ({host})",
            fg="green",
        )

    logging.info("Starting ssh session using: %s", " ".join(ssh_args))
    exit_code = subprocess.call(ssh_args, env=os.environ)
    if exit_code != 0:
        logging.warning("SSH exited with a non-zero exit code. code=%s", exit_code)
    ctx.exit(exit_code)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
