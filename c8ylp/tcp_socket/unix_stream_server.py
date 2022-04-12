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
""" Unix Stream Socket server"""


import os
import logging
import threading
import socketserver

from c8ylp.tcp_socket.tcp_server import TCPProxyServer, TCPHandler


class CustomUnixStreamServer(socketserver.UnixStreamServer):
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
    ) -> None:
        self.allow_reuse_address = True
        self.timeout = tcp_timeout
        self.buffer_size = buffer_size
        self.web_socket_client = web_socket_client
        super().__init__(
            server_address, RequestHandlerClass, bind_and_activate=bind_and_activate
        )


class UnixStreamProxyServer(TCPProxyServer):
    """
    Unix domain socket server
    """

    # pylint: disable=super-init-not-called
    def __init__(
        self,
        path,
        web_socket_client,
        tcp_buffer_size,
        tcp_timeout,
    ):
        self.web_socket_client = web_socket_client
        self._running = threading.Event()
        self.logger = logging.getLogger(__name__)
        self.path = path

        # Expose func to web socket client
        self.web_socket_client.proxy = self

        self.server = CustomUnixStreamServer(
            self.web_socket_client,
            path,
            TCPHandler,
            buffer_size=tcp_buffer_size,
            tcp_timeout=tcp_timeout,
        )

    def shutdown(self):
        """Shutdown tcp server"""
        super().shutdown()
        os.remove(self.path)
