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
"""CLI testing fixtures"""
from typing import Any, Dict, List
from unittest.mock import patch
import responses
from c8ylp.main import cli
from c8ylp.cli.core import CliLogger


def mock_cli():

    with patch("c8ylp.cli.core.start_ssh") as mock:
        yield cli


class FixtureCumulocityAPI:
    def __init__(self, base_url="https://example.c8y.io", tenant="t12345") -> None:
        self.base_url = base_url
        self.tenant = tenant
        pass

    def simulate_pre_authenticated(
        self,
        serial_number: str = "ext-device-01",
        external_type: str = "c8y_Serial",
        tenant: str = None,
        device_managed_object: Dict[str, Any] = None,
        roles: List[str] = None,
    ):
        roles = roles if roles is not None else ["ROLE_REMOTE_ACCESS_ADMIN"]
        self.simulate_loginoptions()
        self.simulate_current_user(roles=roles)
        self.simulate_external_identity(
            serial_number=serial_number, external_type=external_type
        )
        self.simulate_managed_object(fragments=device_managed_object)

    def simulate_loginoptions(
        self, tenant: str = None, roles=["ROLE_REMOTE_ACCESS_ADMIN"]
    ):
        responses.add(
            responses.GET,
            f"{self.base_url}/tenant/loginOptions",
            json={
                "loginOptions": [
                    {
                        "initRequest": f"example?tenantId={tenant or self.tenant}",
                        "type": "OAUTH2_INTERNAL",
                    }
                ]
            },
            status=200,
        )

    def simulate_external_identity(
        self,
        tenant: str = None,
        external_type="c8y_Serial",
        serial_number="ext-device-01",
        managed_object_id="12345",
        code=200,
    ):
        responses.add(
            responses.GET,
            f"{self.base_url}/identity/externalIds/{external_type}/{serial_number}",
            json={
                "managedObject": {
                    "id": managed_object_id,
                },
            },
            status=code,
        )

    def simulate_managed_object(
        self,
        id: str = "12345",
        name: str = "device01",
        fragments: Dict[str, Any] = None,
        code=200,
    ):
        if fragments is None:
            fragments = {
                "c8y_RemoteAccessList": [
                    {
                        "id": "remote-access-id",
                        "name": "Passthrough",
                        "protocol": "PASSTHROUGH",
                        "port": 2001,
                    },
                ],
            }
        responses.add(
            responses.GET,
            f"{self.base_url}/inventory/managedObjects/{id}",
            json={
                "id": id,
                "name": name,
                **fragments,
            },
            status=code,
        )

    def simulate_current_user(self, roles: List[str] = None):
        roles = roles if roles is not None else ["ROLE_REMOTE_ACCESS_ADMIN"]
        user = {
            "effectiveRoles": [],
        }
        for role in roles:
            user["effectiveRoles"].append({"id": role, "name": role})
        responses.add(
            responses.GET, f"{self.base_url}/user/currentUser", json=user, status=200
        )

    def simulate_login_oauth(self, status_codes: List[int]):
        for status in status_codes:
            responses.add(
                responses.POST,
                f"{self.base_url}/tenant/oauth?tenant_id={self.tenant}",
                json={},
                adding_headers=[
                    ("Set-Cookie", "authorization=dummy-token-xyz; path=/; secure"),
                    ("Set-Cookie", "XSRF-TOKEN=my-XSRF-token; path=/; secure"),
                ],
                status=status,
            )
            # responses.add(
            #     responses.POST,
            #     f"{self.base_url}/tenant/oauth?tenant_id={self.tenant}",
            #     status=401,
            # )

        pass


class LocalProxyLog:
    """Local Proxy Log fixture"""

    def print_output(self):
        """Print log output"""
        log_path = CliLogger.log_path()
        if log_path.is_file():
            print(f"--localproxy.log ({log_path})--\n" + log_path.read_text())
