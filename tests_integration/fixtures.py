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
"""Integration fixtures"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Device:
    device: str = ""
    ssh_user: str = ""


class FileFactory:
    """File factory to generate files with random content"""

    def __init__(self, dir: str) -> None:
        self._dir = Path(dir)

    @property
    def dir(self) -> Path:
        """Directory where the temp files are created"""
        return self._dir

    def create_file(self, name: str, size_mb: int = 10) -> Path:
        path = self._dir / name
        with open(path, "wb") as file:
            for i in range(0, size_mb * 1000):
                file.write(os.urandom(1024))

        return path
