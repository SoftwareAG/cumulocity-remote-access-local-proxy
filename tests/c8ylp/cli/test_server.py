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
"""Server tests"""

from unittest.mock import patch

from click.testing import CliRunner
from c8ylp.main import cli


@patch("c8ylp.cli.server.ProxyContext", autospec=True)
def test_server_mode(mock_context):
    """Start a mocked server"""
    mock_context.start.return_value = 0

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["server", "ext-device-01"],
    )
    assert result.exit_code == 0
