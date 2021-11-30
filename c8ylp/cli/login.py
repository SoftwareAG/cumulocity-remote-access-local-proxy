#
# Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""login command"""

import click

from .. import options
from .core import ProxyContext, create_client


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
    """Login and save token to an environment file

    You will be prompted for all of the relevant information,
    i.e. host, username, password and TFA code (if required)

    Example 1: Create/update an env-file by trying to login into Cumulocity

    \b
        c8ylp login --env-file mytenant.env

    """
    opts = ProxyContext(ctx, kwargs)

    try:
        create_client(ctx, opts)
    except Exception:
        ctx.fail("Could not login")
