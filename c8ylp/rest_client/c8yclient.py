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
"""Cumulocity client"""
#  Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
#  SPDX-License-Identifier: Apache-2.0
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

import json
import logging
from typing import Any, Dict

import requests
from requests.auth import HTTPBasicAuth

from c8ylp.rest_client.sessions import BaseUrlSession


class CumulocityMissingTFAToken(Exception):
    """Cumulocity missing TFA token"""


class CumulocityPermissionDeviceError(Exception):
    """Cumulocity device permission error"""

    def __init__(self, user: str, device: str, host: str) -> None:
        message = f"User {user} is not authorized to read Device Data of Device {device} on {host}"
        super().__init__(message)


class CumulocityDeviceNotFound(Exception):
    """Cumulocity device not found error"""

    def __init__(self, device: str, host: str) -> None:
        message = f"A device with the external id '{device}' was not found in Cumulocity host: {host}"
        super().__init__(message)


class BearerAuth(requests.auth.AuthBase):
    """Bearer/token based authorization"""

    # pylint: disable=too-few-public-methods
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r


class CumulocityClient:
    """Cumulocity REST Client"""

    def __init__(
        self,
        hostname: str,
        tenant: str = "",
        user: str = "",
        password: str = "",
        tfacode: str = "",
        token: str = "",
        ignore_ssl_validate: bool = False,
    ):
        hostname = hostname or ""

        if hostname.startswith("http"):
            self.url = hostname
        else:
            self.url = f"https://{hostname}"

        self.session = BaseUrlSession(prefix_url=self.url)

        if ignore_ssl_validate:
            self.session.verify = False

        self.tenant = tenant
        self.user = user
        self.password = password
        self.tfacode = tfacode
        self.token = token
        self._supports_oauth = False

        if token:
            self.set_bearer_auth(token)
        else:
            self.set_basic_auth(user, password)

        self.logger = logging.getLogger(__name__)

    def validate_tenant_id(self) -> str:
        """Validate the tenant id configured in the client
        If it is does not match the Url, then it will be updated to match.

        Returns:
            str: Tenant ID
        """
        tenant_id = ""
        response = self.session.get("/tenant/loginOptions")
        if response.status_code == 200:
            login_options_body = json.loads(response.content.decode("utf-8"))
            login_options = login_options_body.get("loginOptions", dict())
            for option in login_options:

                # Check if oAuth is supported
                if option.get("type") == "OAUTH2_INTERNAL":
                    self._supports_oauth = True

                if "initRequest" in option:
                    _, _, tenant_id = option.get("initRequest", "").partition("=")
                    if self.tenant != tenant_id:
                        if self.tenant:
                            # Skip warning if the tenant id is not set
                            self.logger.warning(
                                "Wrong Tenant ID %s, Correct Tenant ID: %s",
                                self.tenant,
                                tenant_id,
                            )
                        self.tenant = tenant_id
                    else:
                        tenant_id = ""
                    break

        else:
            self.logger.error("Could not validate Tenant ID")
        return tenant_id

    def validate_remote_access_role(self) -> bool:
        """Check if the current user has permission to access the remote access feature
        i.e. the ROLE_REMOTE_ACCESS_ADMIN role.

        Returns:
            bool: True if the user had the correct role assigned to them
        """
        is_valid = False
        response = self.session.get("/user/currentUser")
        if response.status_code == 200:
            user = json.loads(response.content.decode("utf-8"))
            effective_roles = user["effectiveRoles"]
            for role in effective_roles:
                if role.get("id") == "ROLE_REMOTE_ACCESS_ADMIN":
                    self.logger.debug(
                        "Remote Access Role assigned to User %s", self.user
                    )
                    is_valid = True
                    break
        else:
            self.logger.error("Could not get the user's data")
            is_valid = False
        return is_valid

    def set_bearer_auth(self, token: str) -> None:
        """Set authorization header to use a bearer token

        Args:
            token (str): [description]
        """
        self.session.auth = BearerAuth(token)

    def set_basic_auth(self, username: str, password: str) -> None:
        """Set the authorization header to use basic authentication

        Args:
            username (str): Cumulocity username
            password (str): Cumulocity password
        """
        self.session.auth = HTTPBasicAuth(username or "", password or "")

    def validate_credentials(self) -> bool:
        """Validate client's credentials by sending a request

        If the request fails, then the token and password will be configured
        in the client will be set to None.

        Raises:
            PermissionError: Permission error if the credentials are not valid

        Returns:
            bool: True if the credentials were validated
        """
        response = self.session.get("/user/currentUser")
        if response.status_code == 200:
            return True

        message = f"Error validating Token {response.status_code}. Please provide Tenant, User and Password"

        if response.headers.get("content-type") == "application/json":
            response_json = response.json()
            if "message" in response_json:
                message = response_json()

        # clear token/password (as they maybe invalid)
        self.token = ""
        self.password = ""

        error = PermissionError(message)
        self.logger.error(error)
        raise error

    def login(self):
        """Login or validate Cumulocity Credentials.
        For OAuth type logins, a token will be generated (The perferred method).

        If the tenant only has Basic Auth enabled, then the given credentials will
        be validated.
        """
        if self._supports_oauth:
            self.login_oauth()
        else:
            # Basic AUTH does not required login, but validate
            # the credentials
            self.validate_credentials()

    def login_oauth(self):
        """Login via OAuth2 and set the give token if the login is successful

        Raises:
            PermissionError: Error if the provided credentials and/or tfa code are incorrect
            Exception: Unexpected error
        """
        oauth_url = f"/tenant/oauth?tenant_id={self.tenant}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = {
            "grant_type": "PASSWORD",
            "username": self.user,
            "password": self.password,
            "tfa_code": self.tfacode,
        }
        self.logger.debug(
            "Sending requests to %s with body %s",
            oauth_url,
            str(body).replace(str(self.password), "******"),
        )
        self.session.auth = None
        response = self.session.post(oauth_url, headers=headers, data=body)
        if response.status_code == 200:
            self.logger.debug(
                "Authentication successful. Tokens have been updated %s",
                self.session.cookies.get_dict(),
            )
            self.token = self.session.cookies.get_dict()["authorization"]
            self.set_bearer_auth(self.token)
            self.session.headers["X-XSRF-TOKEN"] = self.session.cookies.get_dict()[
                "XSRF-TOKEN"
            ]
        elif response.status_code == 401:
            # Check if TFA is required
            if "TFA" in response.text and not self.tfacode:
                error = CumulocityMissingTFAToken()
            else:
                error = PermissionError(
                    response.json().get(
                        "message", "User is not authorized to access Tenant"
                    ),
                    # f"User {self.user} is not authorized to access Tenant {self.tenant} or TFA-Code is invalid.",
                )
                self.logger.error(error)
            raise error
        else:
            error = Exception(
                f"Server Error received for User {self.user} and Tenant {self.tenant}. "
                f"Status Code: {response.status_code}"
            )
            self.logger.error(error)
            raise error

    def get_external_id(
        self, serial_number: str, identity_type: str = "c8y_Serial"
    ) -> Dict[str, Any]:
        """Get the external id provided the serial number and external id type

        Args:
            serial_number (str): Device external identity
            identity_type (str, optional): External identity type. Defaults to 'c8y_Serial'.

        Raises:
            CumulocityPermissionDeviceError: Error when the user does not have the correct permissions
                to access the API or device
            Exception: Unexpected error

        Returns:
            Dict[str, Any]: External Id definition containing the managed object id
        """
        response = self.session.get(
            f"/identity/externalIds/{identity_type}/{serial_number}"
        )

        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"))

        error = Exception(
            f"Error retrieving device. Status Code {response.status_code}"
        )
        if response.status_code == 401:
            error = CumulocityPermissionDeviceError(self.user, serial_number, self.url)
        elif response.status_code == 404:
            error = CumulocityDeviceNotFound(serial_number, self.url)

        self.logger.error(error)
        raise error

    def get_managed_object(
        self, serial_number: str, identity_type: str = "c8y_Serial"
    ) -> Dict[str, Any]:
        """Get a managed object by looking it up via its external identity

        Args:
            serial_number (str): Device external identity
            identity_type (str, optional): External identity type. Defaults to 'c8y_Serial'.

        Raises:
            CumulocityPermissionDeviceError: Error when the user does not have the correct permissions
                to access the API or device
            Exception: Unexpected error

        Returns:
            Dict[str, Any]: Device managed object
        """
        ext_id = self.get_external_id(serial_number, identity_type)
        mor_id = ext_id.get("managedObject", dict()).get("id")

        if not mor_id:
            raise Exception("Managed object id is empty")

        response = self.session.get(f"/inventory/managedObjects/{mor_id}")
        if response.status_code == 200:
            return json.loads(response.content.decode("utf-8"))

        error = Exception(
            f"Error retrieving device. Status Code {response.status_code}, "
            f"device (external id)={serial_number}, host={self.url}, user={self.user}"
        )
        if response.status_code == 401:
            error = CumulocityPermissionDeviceError(self.user, serial_number, self.url)
        elif response.status_code == 404:
            error = CumulocityDeviceNotFound(serial_number, self.url)

        self.logger.error(error)
        raise error
