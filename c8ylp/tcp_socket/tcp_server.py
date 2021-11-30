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
"""TCP server"""

import errno
import logging
import socket
import socketserver
import threading


class TCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server
    """

    def handle(self):
        """Websocket connection handler"""
        request: socket.socket = self.request

        laddr = request.getsockname()
        raddr = request.getpeername()
        logging.info(
            "Handling request: fd=%s, laddr=%s, raddr=%s",
            request.fileno(),
            laddr,
            raddr,
        )

        def handle_shutdown():
            # Force shutdown of any socket reads or writes
            request.shutdown(socket.SHUT_RDWR)

        self.server.web_socket_client.shutdown_request = handle_shutdown

        # connect websocket
        if not self.server.web_socket_client.is_open():
            self.server.web_socket_client.connect()

        # update link to current tcp socket send
        request_error = False

        def safe_send(data):
            nonlocal request_error
            try:
                if not request_error:
                    request.send(data)
            except OSError as ex:
                request_error = True
                if ex.errno == errno.EBADF:
                    # TODO: Check what is sending messages after it has been closed
                    logging.info("Ignoring Bad file descriptor")
                else:
                    logging.error(ex)

        self.server.web_socket_client.proxy_send_message = safe_send

        while True:
            try:
                logging.debug("Reading from tcp port")
                data = request.recv(self.server.buffer_size or 1024)
                logging.debug("%s wrote: %s", self.client_address, data)

                if not data:
                    logging.debug("No data. Request will be closed")
                    self.server.web_socket_client.proxy_send_message = None
                    break

                logging.debug("Writing data to ws: %s", data)
                self.server.web_socket_client.send_binary(data)
                logging.debug("Wrote data to ws: %s", data)
            except ConnectionResetError as ex:
                logging.info("Connection was reset. %s", ex)
                break


class CustomTCPServer(socketserver.TCPServer):
    """Custom TCP Server used to listen for local connections and proxy them to
    a websocket
    """

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
        self.timeout = tcp_timeout
        self.buffer_size = buffer_size
        self.web_socket_client = web_socket_client
        super().__init__(
            server_address, RequestHandlerClass, bind_and_activate=bind_and_activate
        )


class TCPProxyServer:
    """TCP Server"""

    def __init__(
        self,
        port,
        web_socket_client,
        tcp_buffer_size,
        tcp_timeout,
    ):
        self.web_socket_client = web_socket_client
        self._running = threading.Event()
        self.logger = logging.getLogger(__name__)

        # Expose func to web socket client
        self.web_socket_client.proxy = self

        self.server = CustomTCPServer(
            self.web_socket_client,
            ("localhost", port),
            TCPHandler,
            port=port,
            buffer_size=tcp_buffer_size,
            tcp_timeout=tcp_timeout,
        )

    def serve_forever(self):
        """Server tcp server forever. Only returns once .shutdown has been called"""
        self._running.set()
        try:
            self.server.serve_forever()
        except Exception as ex:
            logging.error("TCP Server raised an exception. %s", ex, exc_info=True)
            raise ex
        self._running.clear()

    def shutdown(self):
        """Shutdown tcp server"""
        if self._running.is_set():
            logging.info("Shutting down TCP server")
            self.server.shutdown()

    def wait_for_running(self, timeout: float = 30.0) -> bool:
        """Wait for the server to startup

        Args:
            timeout (float, optional): Timeout in seconds. Defaults to 30.0.

        Returns:
            bool: True if the server is running
        """
        return self._running.wait(timeout)
