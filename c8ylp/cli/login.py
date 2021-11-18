"""login command"""

import click

from .. import options
from .core import ProxyOptions, create_client


@click.command()
@options.HOSTNAME_PROMPT
@options.C8Y_TENANT
@options.C8Y_USER
@options.C8Y_TOKEN
@options.C8Y_PASSWORD
@options.C8Y_TFA_CODE
@options.LOGGING_VERBOSE
@options.ENV_FILE_OPTIONAL_EXISTS
@options.STORE_TOKEN
@options.DISABLE_PROMPT
@click.pass_context
def login(
    ctx: click.Context,
    *_args,
    **kwargs,
):
    """Login and save credentials to an environment file

    You will be prompted for all of the relevant information,
    i.e. host, username, password and TFA code (if required)

    Example: Create/update an env-file by trying to login into Cumulocity
    \b
        c8ylp login --env-file mytenant.env

    """
    opts = ProxyOptions().fromdict(kwargs)

    try:
        create_client(ctx, opts)
    except Exception:
        ctx.fail("Could not login")
