"""TCP server"""
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
import socket
import socketserver
import threading
import platform
import os
import signal


class ProxyInterface:
    def send_message(self):
        pass

    def shutdown(self):
        pass


class TCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server
    """

    def setup(self) -> None:
        return super().setup()

    def handle(self):
        # self.request is the TCP socket connected to the client
        request: socket.socket = self.request
        logging.info("Handling request: %s", request)

        self.server.active_request = request
        while True:
            try:
                data = request.recv(1024)
                logging.debug("%s wrote: %s", self.client_address, data)

                if not data:
                    logging.info("No data. Request will be closed")
                    break

                if (
                    self.server.web_socket_client
                    and self.server.web_socket_client.is_ws_available()
                ):
                    logging.debug("Writing data to ws: %s", data)
                    self.server.web_socket_client.web_socket.sock.send_binary(data)
            except ConnectionResetError as ex:
                logging.info("Connection was reset. %s", ex)
                break

        self.server.active_request = None


class CustomTCPServer(socketserver.TCPServer):
    def __init__(
        self,
        web_socket_client,
        server_address,
        RequestHandlerClass,
        bind_and_activate=True,
        buffer_size: int = 1024,
        tcp_timeout: float = 30,
        port: int = None,
    ) -> None:
        self.allow_reuse_address = True
        self.port = port
        self.buffer_size = buffer_size
        self.web_socket_client = web_socket_client
        self.active_request = None
        super().__init__(
            server_address, RequestHandlerClass, bind_and_activate=bind_and_activate
        )


class TCPServer:
    """TCP Server"""

    def __init__(
        self,
        port,
        web_socket_client,
        tcp_buffer_size,
        tcp_timeout,
        script_mode,
        max_reconnects=5,
    ):
        self.web_socket_client = web_socket_client
        self.script_mode = script_mode
        self._running = threading.Event()
        self.logger = logging.getLogger(__name__)
        self.server = CustomTCPServer(
            self.web_socket_client,
            ("localhost", port),
            TCPHandler,
            port=port,
            buffer_size=tcp_buffer_size,
            tcp_timeout=tcp_timeout,
        )

        self.max_reconnects = max_reconnects
        self.reconnect_counter = 0

    def send_message(self, data):
        if self.server and self.server.active_request:
            self.server.active_request.send(data)

    def shutdown_request(self):
        if self.server.active_request:
            self.logger.info("Shutting down request")
            self.server.shutdown_request(self.server.active_request)

        # trigger a reconnect (if not in script mode)
        self.handle_reconnect()

    def handle_reconnect(self):
        if not self.script_mode and (
            self.max_reconnects == 0 or self.reconnect_counter < self.max_reconnects
        ):
            self.logger.info("Reconnect with counter %s", self.reconnect_counter)
            self.reconnect_counter += 1
            self.web_socket_client.reconnect()
        else:
            # Force shutdown
            self.shutdown()

    def serve_forever(self):
        self._running.set()
        self.server.serve_forever()
        self._running.clear()

    def shutdown(self):
        if self._running.is_set():
            logging.info("Shutting down TCP server")
            if self.server.active_request:
                self.server.shutdown_request(self.server.active_request)
            self.server.shutdown()
