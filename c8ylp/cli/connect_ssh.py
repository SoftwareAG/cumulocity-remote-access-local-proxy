"""connect-ssh command"""

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
@options.PORT_DEFAULT_RANDOM
@options.PING_INTERVAL
@options.TCP_SIZE
@options.TCP_TIMEOUT
@options.LOGGING_VERBOSE
@options.SSL_IGNORE_VERIFY
@options.SSH_USER
@options.ENV_FILE
@options.STORE_TOKEN
@options.DISABLE_PROMPT
@click.argument(
    "additional_args", metavar="[REMOTE_COMMANDS]...", nargs=-1, type=click.UNPROCESSED
)
@click.pass_context
def connect_ssh(
    ctx,
    *_args,
    **kwargs,
):
    """Start once-off proxy and connect via ssh

    An interactive ssh is opened if a remote command is not provided.

    Once the ssh session is closed, then the local proxy will be shutdown.

    Use "--" before the remote commands to prevent the arguments
    from being interpreted by c8ylp (i.e. to avoid clashes with c8ylp).

    \b
        DEVICE is the device's external identity

    Example 1: Start an interactive SSH connection

    \b
        c8ylp connect-ssh --env-file .env device01 --ssh-user admin

    Example 2: Execute a command via SSH

    \b
        c8ylp connect-ssh --env-file .env device01 --ssh-user admin -- systemctl status ssh

    Example 3: Execute a complex command via SSH (use quotes to ensure command is sent to the device)

    \b
        c8ylp connect-ssh --env-file .env device01 --ssh-user admin -- "systemctl status ssh; dpkg --list | grep ssh"

    """
    opts = ProxyOptions().fromdict(kwargs)
    opts.script_mode = True
    start_proxy(ctx, opts)
