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
"""Test sessions"""

import responses
from c8ylp.rest_client.sessions import BaseUrlSession


@responses.activate
def test_session_with_partial_urls():
    """Test expansion of partial urls when sending requests"""
    session = BaseUrlSession("example.c8y.io")

    responses.add(
        "GET",
        url="https://example.c8y.io/partial/url",
    )
    response = session.get("/partial/url")
    assert response.status_code == 200
    assert response.url == "https://example.c8y.io/partial/url"


@responses.activate
def test_session_with_full_url():
    """Test handling of full urls. The hostname should be left untouched"""
    session = BaseUrlSession("example.c8y.io")

    responses.add(
        "GET",
        url="https://someotherurl.com/hello",
    )
    response = session.get("https://someotherurl.com/hello")
    assert response.status_code == 200
    assert response.url == "https://someotherurl.com/hello"
