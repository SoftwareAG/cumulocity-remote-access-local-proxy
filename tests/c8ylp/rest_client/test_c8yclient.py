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
"""Cumulocity client tests"""

from c8ylp.rest_client.c8yclient import CumulocityClient


def test_client_defaults_to_https():
    """Test that client defaults to using https"""
    assert CumulocityClient("example.c8y.io").url == "https://example.c8y.io"
    assert CumulocityClient("https://example.c8y.io").url == "https://example.c8y.io"
    assert CumulocityClient("http://example.c8y.io").url == "http://example.c8y.io"
