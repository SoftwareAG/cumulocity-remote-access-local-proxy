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
"""Main cli interface to c8ylp"""

import click

from .cli.login import login
from .cli.plugin import cli_plugin
from .cli.server import server
from .cli.version import version
from .cli.connect import commands as connect

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group()
def cli_core():
    """Main cli entry point"""


cli_core.add_command(login)
cli_core.add_command(version)
cli_core.add_command(server)
cli_core.add_command(connect.connect)

cli = click.CommandCollection(
    "cli",
    sources=[cli_core, cli_plugin],
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
    no_args_is_help=True,
    help="Cumulocity Remote Access Local Proxy",
)
