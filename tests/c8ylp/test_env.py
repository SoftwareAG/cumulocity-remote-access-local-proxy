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
"""Environment file tests"""
import os
import pathlib

from c8ylp.env import loadenv, save_env


def test_load_env_from_file(tmp_path: pathlib.Path):
    """Test loading environment variables from file"""
    envfile = tmp_path / ".env"

    envfile.write_text(
        "\n".join(
            [
                "VALUE1=three",
                "#VALUE1=one",
                ";VALUE1=two",
                "value2=some other value",
                "value3='quoted value $value2'",
                'expanded_value="quoted value $value2"',
            ]
        )
    )

    loadenv(str(envfile))

    assert os.environ["VALUE1"] == "three"
    assert os.environ["value2"] == "some other value"
    assert os.environ["value3"] == "quoted value $value2"
    assert os.environ["expanded_value"] == "quoted value some other value"


def test_save_env_file(tmp_path: pathlib.Path):
    """Testing saving configuration from env file"""
    envfile = tmp_path / ".env"

    envfile.write_text(
        "\n".join(
            [
                "value2=existing value",
            ]
        )
    )

    assert save_env(
        str(envfile),
        {
            "VALUE1": "three",
            "value2": "some other value",
            "value3": "quoted value $value2",
            "expanded_value": "quoted value some other value",
        },
    )

    contents = envfile.read_text()
    assert contents == "\n".join(
        [
            "value2=some other value",
            "VALUE1=three",
            "value3=quoted value $value2",
            "expanded_value=quoted value some other value\n",
        ]
    )
