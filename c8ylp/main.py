#!/usr/bin/env python
"""Main cli interface to c8ylp"""
# -*- coding: utf-8 -*-

#  Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
#  SPDX-License-Identifier: Apache-2.0
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import click

from .cli.connect_ssh import connect_ssh
from .cli.execute import execute
from .cli.login import login
from .cli.plugin import plugin
from .cli.server import server
from .cli.version import version


@click.group(
    invoke_without_command=True,
    no_args_is_help=True,
    context_settings=dict(
        help_option_names=["-h", "--help"],
    ),
    help="Cumulocity Remote Access Local Proxy",
)
@click.pass_context
def cli_core(ctx: click.Context):
    """Main cli entry point"""
    ctx.ensure_object(dict)


cli_core.add_command(login)
cli_core.add_command(version)
cli_core.add_command(server)
cli_core.add_command(execute)
cli_core.add_command(connect_ssh)

cli = click.CommandCollection("cli", sources=[cli_core, plugin])
