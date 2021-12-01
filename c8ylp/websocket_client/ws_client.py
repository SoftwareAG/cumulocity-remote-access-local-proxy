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
"""Websocket client"""
import logging
import threading
import ssl
from typing import Any, Callable

import websocket
import certifi


WEBSOCKET_CLOSE_REASONS = {
    websocket.STATUS_NORMAL: "NORMAL",
    websocket.STATUS_GOING_AWAY: "GOING_AWAY",
    websocket.STATUS_PROTOCOL_ERROR: "PROTOCOL_ERROR",
    websocket.STATUS_UNSUPPORTED_DATA_TYPE: "UNSUPPORTED_DATA_TYPE",
    websocket.STATUS_STATUS_NOT_AVAILABLE: "STATUS_NOT_AVAILABLE",
    websocket.STATUS_ABNORMAL_CLOSED: "ABNORMAL_CLOSED",
    websocket.STATUS_INVALID_PAYLOAD: "INVALID_PAYLOAD",
    websocket.STATUS_POLICY_VIOLATION: "POLICY_VIOLATION",
    websocket.STATUS_MESSAGE_TOO_BIG: "MESSAGE_TOO_BIG",
    websocket.STATUS_INVALID_EXTENSION: "INVALID_EXTENSION",
    websocket.STATUS_UNEXPECTED_CONDITION: "UNEXPECTED_CONDITION",
    websocket.STATUS_BAD_GATEWAY: "BAD_GATEWAY",
    websocket.STATUS_TLS_HANDSHAKE_ERROR: "TLS_HANDSHAKE_ERROR",
}


def lookup_close_status_code(code: int) -> str:
    """Lookup the websocket close status code and return a user friendly string
    If the status code is unknown then it will be returned as a string without
    a meaningful status.

    Args:
        code (int): Websocket close status/code

    Returns:
        str: Close status as text
    """
    if code in WEBSOCKET_CLOSE_REASONS:
        return f"{code} ({WEBSOCKET_CLOSE_REASONS[code]})"

    return str(code)


class WebsocketClient(threading.Thread):
    """Websocket client"""

    def __init__(
        self,
        host,
        config_id,
        device_id,
        session,
        token,
        ignore_ssl_validate=False,
        ping_interval=0,
        max_retries=0,
        shutdown_request=None,
    ):
        self.host = host
        self.config_id = config_id
        self.device_id = device_id
        self.web_socket = None
        self.proxy = None
        self._ws_open_event = threading.Event()
        self._ws_timeout = 10
        self._ws_ping_interval = ping_interval
        # ping timeout must be less than the interval, so just take a percentage
        self._ws_ping_timeout = ping_interval * 0.9 if ping_interval > 0 else None
        self.logger = logging.getLogger(__name__)
        self.wst = None
        self.session = session
        self.token = token
        self.ws_handshake_error = False
        self.ignore_ssl_validate = ignore_ssl_validate
        self.max_retries = max_retries
        self.connection_attempts = 0
        self.shutdown_request = shutdown_request
        self._connection_stable_timer = None
        self._connection_stable_sec = 10

        self.proxy_send_message: Callable = None
        super().__init__()

    def connect(self):
        """Connect websocket"""
        self._ws_open_event.clear()

        # increment before logic as when reconnect is called, then it
        self.connection_attempts += 1

        # websocket.enableTrace(True) # Enable this for Debug Purpose only
        if self.host.startswith("https"):
            self.host = self.host.replace("https", "wss")
        elif self.host.startswith("http"):
            self.host = self.host.replace("http", "wss")
        elif not self.host.startswith("wss://"):
            self.host = f"wss://{self.host}"
        url = f"{self.host}/service/remoteaccess/client/{self.device_id}/configurations/{self.config_id}"
        self.logger.info("Connecting to WebSocket with URL %s", url)

        if self.token:
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + self.token,
            }
            self.web_socket = websocket.WebSocketApp(url, header=headers)
        else:
            headers = {
                "Content-Type": "application/json",
            }
            if "XSRF-TOKEN" in self.session.cookies.get_dict():
                headers["X-XSRF-TOKEN"] = self.session.cookies.get_dict()["XSRF-TOKEN"]
            cookies = self.session.cookies.get_dict()
            cookie_string = "; ".join(
                [str(x) + "=" + str(y) for x, y in cookies.items()]
            )
            self.web_socket = websocket.WebSocketApp(
                url, header=headers, cookie=cookie_string
            )
        # self.logger.debug(f'Cookie String: {cookie_string}')

        # pylint: disable=unnecessary-lambda
        # See https://stackoverflow.com/questions/26980966/using-a-websocket-client-as-a-class-in-python
        self.web_socket.on_message = lambda ws, msg: self._on_ws_message(ws, msg)
        self.web_socket.on_error = lambda ws, error: self._on_ws_error(ws, error)
        self.web_socket.on_close = lambda ws, msg, msg2: self._on_ws_close(
            ws, msg, msg2
        )
        self.web_socket.on_open = lambda ws: self._on_ws_open(ws)

        # Note: Don't use a ping interval as it can cause the connection to be closed
        web_socket_kwargs = {
            "ping_interval": self._ws_ping_interval,
            "ping_timeout": self._ws_ping_timeout,
        }

        # Load ca certificates
        sslopt_ca_certs = {"ca_certs": certifi.where()}

        if self.ignore_ssl_validate:
            sslopt_ca_certs["cert_reqs"] = ssl.CERT_NONE
        web_socket_kwargs["sslopt"] = sslopt_ca_certs

        self.logger.debug("websocket options: %s", web_socket_kwargs)

        self.wst = threading.Thread(
            target=self.web_socket.run_forever, kwargs=web_socket_kwargs
        )
        self.wst.daemon = True
        self.wst.name = f"WSTunnelThread-{self.config_id}"
        self.wst.start()
        return self

    def reconnect(self):
        """Reconnect websocket"""
        if self.web_socket:
            self.web_socket.close()

        if self.max_retries > -1 and self.connection_attempts >= self.max_retries:
            if callable(self.shutdown_request):
                self.logger.debug("Websocket is requesting the server to stop")
                self.shutdown_request()

            return

        self.logger.info(
            "Reconnecting to WebSocket: reconnects=%d, max=%d",
            self.connection_attempts,
            self.max_retries,
        )

        self.web_socket = None
        self.connect()

    def stop(self):
        """Stop websocket"""
        # Closing WebSocket
        self.logger.debug("Stopping WebSocket Connection")

        if self.web_socket:
            self.web_socket.close()
        self.web_socket = None

    def is_ws_available(self) -> bool:
        """Check if websocket is open

        Returns:
            bool: True if the websocket is open
        """
        return self._ws_open_event.wait(timeout=self._ws_timeout)

    def is_open(self) -> bool:
        """Check if websocket is open

        Returns:
            bool: True if the websocket is open
        """
        return self._ws_open_event.is_set()

    def send_binary(self, data: Any) -> None:
        """Send binary data to websocket

        Args:
            data (Any): Data / message to be sent
        """
        if self.web_socket and self.is_ws_available():
            self.web_socket.sock.send_binary(data)

    def _on_ws_message(self, _ws, message):
        try:
            self.logger.debug("WebSocket Message received: %s", message)

            self.logger.debug("Sending to TCP Socket: %s", message)
            if self.proxy_send_message and callable(self.proxy_send_message):
                # pylint: disable=not-callable
                self.proxy_send_message(message)

        except Exception as ex:
            self.logger.error("Error on handling WebSocket Message %s: %s", message, ex)
            self.stop()

    def _on_ws_error(self, _ws, error):
        self.logger.debug("Type of WS Error %s", type(error))
        if hasattr(error, "status_code"):
            self.logger.error(
                "WebSocket Error received: %s with status %s", error, error.status_code
            )
            if error.status_code == 401:
                self.ws_handshake_error = True
                self._ws_open_event.clear()
                self.stop()
                return

        if isinstance(error, websocket.WebSocketTimeoutException):
            self.logger.info(
                "Device %s seems to be offline. No connection possible.", self.device_id
            )
            # Stop websocket
            self.stop()
        else:
            self.logger.error("WebSocket Error received: %s", error)

    def _on_ws_close(self, _ws, close_status, close_reason):
        reason = ""
        if close_reason or close_status != websocket.STATUS_NORMAL:
            reason = f", Reason: {close_reason}"

        self.logger.info(
            "WebSocket Connection closed. Status: %s%s",
            lookup_close_status_code(close_status),
            reason,
        )
        self._ws_open_event.clear()
        self._connection_timer_cancel()
        self.reconnect()

    def _reset_connection_attempts(self):
        """Reset the connection attempts by using a stability timer to ensure that the
        connection is running for a minimum period before the connection attempts
        counter is reset.

        This avoids problems when the device side proxy establishing a connection briefly
        and then closes it due to local device problems such as the ssh daemon not running
        on the device.
        """

        def reset_connection_attempts():
            self.connection_attempts = 0

        if not self._connection_stable_timer:
            self._connection_stable_timer = threading.Timer(
                self._connection_stable_sec,
                reset_connection_attempts,
            )
            self._connection_stable_timer.setName("ws-stable-connection-timer")
            self._connection_stable_timer.daemon = True
            self._connection_stable_timer.start()

    def _connection_timer_cancel(self):
        """Cancel the connection stability timer (if it is already set)"""
        if self._connection_stable_timer is not None:
            self._connection_stable_timer.cancel()
            self._connection_stable_timer = None

    def _on_ws_open(self, _ws):
        self.logger.info("WebSocket Connection opened")
        self._reset_connection_attempts()
        self._ws_open_event.set()
