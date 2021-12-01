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
"""Test environment"""

import os
from typing import Any, Dict
from c8ylp.env import loadenv


class Environment:
    def __init__(self, file=".env") -> None:
        if os.path.exists(file):
            loadenv(file)

        self.data = os.environ

    def env(self) -> Dict[str, str]:
        return self.data

    def create_empty_env(self) -> Dict[str, Any]:
        empty_env = {}
        for key in self.data:
            if key.startswith("C8Y"):
                empty_env[key] = None
        return empty_env

    def create_authenticated(self) -> Dict[str, Any]:
        return {
            "C8Y_HOST": "https://example.c8y.io",
            "C8Y_TENANT": "t12345",
            "C8Y_USER": "user01",
            "C8Y_TOKEN": "dummy-token",
        }

    def create_username_password(self) -> Dict[str, Any]:
        return {
            "C8Y_HOST": "https://example.c8y.io",
            "C8Y_TENANT": "t12345",
            "C8Y_USER": "user01",
            "C8Y_PASSWORD": "som4-p4$swurd",
        }


ENV = Environment()
