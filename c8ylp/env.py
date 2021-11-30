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
"""Environment utilities"""

import os
import pathlib
from collections import defaultdict
from typing import Any, Dict


def loadenv(path: str) -> None:
    """Load environment variables from file

    Lines are ignored if they match any of the following
     * Empty line (only whitespace)
     * Lines starts with "#"
     * Lines starts with ";"

    Values may contain references to other environment variables by
    using "$NAME" or "${NAME}" syntax.

    Values with single or double quotes will be stripped from the value.

    Below is an example of a dotenv file:
    >>>
    ENV1=MYVALUE
    CUSTOMER_NAME="$USER"

    # Literal values can be surrounded with single quotes.
    CUSTOMER_NAME='$USER'
    >>>

    Args:
        path (str): Dotenv file path
    """
    with open(path, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            key, _, value = line.partition("=")

            if value.startswith("'") and value.endswith("'"):
                # Strip single quote wrapping, and skip env expansion
                value = value.strip("'")
            elif value.startswith('"') and value.endswith('"'):
                # Strip surrounding quotes
                value = os.path.expandvars(value.strip('"'))
            else:
                value = os.path.expandvars(value)

            os.environ[key] = value


def save_env(path: str, values: Dict[str, Any]) -> bool:
    """Save a new value to an environment file. If the key already
    exists, then it will be updated in place, otherwise it will be appended.

    If the file does not exist, then it will be created.

    The order of the environment variables are preserved

    Args:
        path (str): file path
        values (Dict[str, Any]): New key/value pairs to add to env file

    Returns:
        bool: True if the file has been changed
    """
    env_file = pathlib.Path(path)
    has_changed = False
    output = [] if not env_file.exists() else env_file.read_text().splitlines()

    key_indexes = defaultdict(lambda: [])

    # collect line indexes of key in existing env file
    for i, line in enumerate(output):
        key, _, _ = line.partition("=")
        if key:
            key_indexes[key].append(i)

    # updates values (if changed, and keep order)
    for key, value in values.items():
        d_value = value if value is not None else ""
        newline = f"{key}={d_value}"

        if key in key_indexes:
            # existing key (update if changed)
            for existing_index in key_indexes[key]:
                if output[existing_index] != newline:
                    output[existing_index] = newline
                    has_changed = True
        else:
            # new key
            output.append(newline)
            has_changed = True

    if has_changed:
        env_file.write_text("\n".join(output).rstrip("\n") + "\n")

    return has_changed
