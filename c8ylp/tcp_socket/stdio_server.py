#
# Copyright (c) 2022 Software AG, Darmstadt, Germany and/or its licensors
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
""" Stdin/Stdout forwarding server"""
import io
import logging
import sys
import threading

from c8ylp.tcp_socket.tcp_server import TCPProxyServer


class StdioHandler:
    """
    The request handler class for our server.

    It is instantiated once and used to forward stdin/stdout to the websocket
    """

    def __init__(self, web_socket_client, buffer_size):
        self.web_socket_client = web_socket_client
        self.buffer_size = buffer_size
        self.shutdown_event = threading.Event()
        self.socket = None
        self._reader = None
        self._writer = None

    def shutdown(self):
        """Shutdown tcp server"""
        self.shutdown_event.set()
        self._reader.close()
        self._writer.close()

    def serve_forever(self):
        """stdio "connection" handler"""
        with io.open(
            sys.stdin.fileno(), mode="rb", closefd=False, buffering=0
        ) as self._reader, io.open(
            sys.stdout.fileno(), mode="wb", closefd=False, buffering=0
        ) as self._writer:
            self.web_socket_client.shutdown_request = self.shutdown

            # connect websocket
            if not self.web_socket_client.is_open():
                self.web_socket_client.connect()

            # update link to current stdin/stdout send
            request_error = False

            def safe_send(data):
                nonlocal request_error
                try:
                    if not request_error:
                        self._writer.write(data)
                except OSError as ex:
                    request_error = True
                    logging.error(ex)

            self.web_socket_client.proxy_send_message = safe_send

            while not self.shutdown_event.is_set():
                try:
                    logging.debug("Reading from stdin")
                    data = self._reader.read(self.buffer_size or 1024)
                    logging.debug("stdin wrote: %s", data)
                    if not data:
                        logging.debug("No data. Request will be closed")
                        self.web_socket_client.proxy_send_message = None
                        self.web_socket_client.stop()
                        break

                    logging.debug("Writing data to ws: %s", data)
                    self.web_socket_client.send_binary(data)
                    logging.debug("Wrote data to ws: %s", data)
                except (ConnectionResetError, OSError) as ex:
                    logging.info("Connection was reset. %s", ex)
                    break


class StdioProxyServer(TCPProxyServer):
    """
    Stdin/Stdout forwarding server
    """

    # pylint: disable=super-init-not-called
    def __init__(
        self,
        web_socket_client,
        buffer_size,
    ):
        self.web_socket_client = web_socket_client
        self._running = threading.Event()
        self.logger = logging.getLogger(__name__)

        # Expose func to web socket client
        self.web_socket_client.proxy = self

        self.server = StdioHandler(self.web_socket_client, buffer_size)
