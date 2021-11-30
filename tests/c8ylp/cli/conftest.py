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
"""SSH command tests"""
import os
from unittest.mock import Mock, patch

import pytest
from c8ylp.rest_client.c8yclient import CumulocityClient
from tests.env import Environment
from tests.fixtures import FixtureCumulocityAPI, LocalProxyLog


@pytest.fixture(name="c8yclient")
def fixture_c8yclient():
    """Cumulocity client fixture"""
    dummy_client = CumulocityClient("https://example.c8y.io")

    def set_tenant():
        dummy_client.tenant = "t12345"
        return dummy_client.tenant

    dummy_client.validate_tenant_id = Mock(side_effect=set_tenant)

    with patch("c8ylp.main.CumulocityClient", return_value=dummy_client) as mock_client:
        yield mock_client


@pytest.fixture(name="env")
def fixture_env():
    """Environment fixture"""
    yield Environment()


@pytest.fixture(name="c8yserver")
def fixture_c8yserver():
    """Cumulocity server fixture to simulate server responses"""
    api = FixtureCumulocityAPI()
    yield api


@pytest.fixture(name="localproxy_log")
def fixture_localproxy_log():
    """Local proxy log fixture"""
    log = LocalProxyLog()
    yield log


@pytest.fixture(autouse=True)
def run_before_and_after_tests(localproxy_log: LocalProxyLog, tmpdir):
    """Fixture to execute asserts before and after a test is run"""
    # Setup: Clear any existing logs
    os.environ["C8YLP_LOG_DIR"] = str(tmpdir)

    yield

    # Show log log output
    localproxy_log.print_output()
