"""execute command"""

import logging

import click
from c8ylp import options

from .core import ProxyOptions, start_proxy


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@options.ARG_DEVICE
@options.ARG_SCRIPT
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
@options.ENV_FILE
@options.STORE_TOKEN
@options.DISABLE_PROMPT
@click.argument(
    "additional_args", metavar="[SCRIPT_ARGS]...", nargs=-1, type=click.UNPROCESSED
)
@click.pass_context
def execute(
    ctx,
    *_args,
    **kwargs,
):
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
        c8ylp execute device01 --env-file .env \\
            -- /usr/bin/scp -P '$PORT' myfile.tar.gz admin@localhost:/tmp

    Example 2: Run a custom script (not included) to copy a file from the device to
    the current folder

        \b
        c8ylp execute device01 --env-file .env -v ./copyfrom.sh /var/log/dpkg.log ./
    """
    opts = ProxyOptions().fromdict(kwargs)
    opts.script_mode = True
    logging.info(
        "Collected additional args which will be passed to script later: %s",
        opts.additional_args,
    )
    start_proxy(ctx, opts)
