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
