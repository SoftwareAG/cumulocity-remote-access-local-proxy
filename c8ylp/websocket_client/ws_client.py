"""Websocket client"""
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

import logging
import threading
import platform

import ssl
import os
import signal
import websocket
import certifi


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
        reconnects=5,
        ping_interval=0,
    ):
        self.host = host
        self.config_id = config_id
        self.device_id = device_id
        self.web_socket = None
        self.tcp_server = None
        self._ws_open_event = None
        self._ws_open = False
        self._ws_timeout = 10
        self._ws_ping_interval = ping_interval
        # ping timeout must be less than the interval, so just take a percentage
        self._ws_ping_timeout = ping_interval * 0.9 if ping_interval > 0 else None
        self.logger = logging.getLogger(__name__)
        self.wst = None
        self.session = session
        self.token = token
        self.trigger_reconnect = reconnects >= 0
        self.reconnect_counter = 0
        self.ws_handshake_error = False
        self.ignore_ssl_validate = ignore_ssl_validate
        self.max_reconnects = reconnects
        super().__init__()

    def connect(self):
        """Connect websocket"""
        self._ws_open_event = threading.Event()
        # websocket.enableTrace(True) # Enable this for Debug Purpose only
        if self.host.startswith("https"):
            self.host = self.host.replace("https", "wss")
        elif self.host.startswith("http"):
            self.host = self.host.replace("http", "wss")
        elif not self.host.startswith("wss://"):
            self.host = f"wss://{self.host}"
        url = f"{self.host}/service/remoteaccess/client/{self.device_id}/configurations/{self.config_id}"
        self.logger.info("Connecting to WebSocket with URL %s ...", url)

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
        return self.wst

    def reconnect(self):
        """Reconnect websocket"""
        self.reconnect_counter += 1
        self.logger.info("Reconnecting to WebSocket...")
        if self.web_socket:
            self.web_socket.keep_running = False
            self.web_socket.close()
        self.web_socket = None
        self.connect()

    def stop(self):
        """Stop websocket"""
        # Closing WebSocket
        self.logger.debug("Stopping WebSocket Connection...")
        self.trigger_reconnect = False
        self.tcp_server.stop_connection()
        if self.web_socket:
            self.web_socket.keep_running = False
            self.web_socket.close()
        self.web_socket = None

    def is_ws_available(self) -> bool:
        """Check if websocket is open

        Returns:
            bool: True if the websocket is open
        """
        if self._ws_open:
            return True
        self._ws_open_event.wait(timeout=self._ws_timeout)
        return self._ws_open

    def _on_ws_message(self, _ws, message):
        try:
            self.logger.debug("WebSocket Message received: %s", message)
            if self.tcp_server.is_tcp_socket_connected():
                if self.tcp_server.connection is not None:
                    self.logger.debug("Sending to TCP Socket: %s", message)
                    self.tcp_server.connection.send(message)
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
                self._ws_open = False
                self._ws_open_event.set()
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
        self.logger.info(
            "WebSocket Connection closed. Status: %s, Reason: %s", close_status, close_reason
        )
        self._ws_open = False
        self._ws_open_event.set()
        if self.tcp_server.is_tcp_socket_available():
            self.tcp_server.connection.send(b"FIN")
            self.tcp_server.stop_connection()
        # else:
        if self.trigger_reconnect and (
            self.max_reconnects == 0 or self.reconnect_counter < self.max_reconnects
        ):
            self.logger.info("Reconnect with counter %s", self.reconnect_counter)
            self.reconnect()
        else:
            if platform.system() in ("Linux", "Darwin"):
                os.kill(os.getpid(), signal.SIGUSR1)
            else:
                os.kill(os.getpid(), signal.SIGINT)

    def _on_ws_open(self, _ws):
        self.logger.info("WebSocket Connection opened!")
        self._ws_open = True
        self._ws_open_event.set()
