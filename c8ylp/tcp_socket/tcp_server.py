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
import sys
import threading


class TCPServer:

    def __init__(self, port, web_socket_client, tcp_buffer_size, tcp_timeout, wst, script_mode):
        self.port = port
        self.sock = None
        self.connection = None
        self.web_socket_client = web_socket_client
        self.tcp_open_event = None
        self.tcp_buffer_size = tcp_buffer_size
        self.conn_is_closed = False
        self.tcp_timeout = tcp_timeout
        self._tcp_open_event = threading.Event()
        self.wst = wst
        self.tcp_timeout_counter = None
        self.script_mode = script_mode
        self.logger = logging.getLogger(__name__)

    def start(self):
        if self.web_socket_client.is_ws_available():
            self._start_server()
            self._start_connection()

    def _start_connection(self):
        try:
            # Listen for incoming connections
            self.conn_is_closed = False
            self._tcp_timeout_counter = 0
            self._tcp_open_event = threading.Event()
            self.sock.listen(1)
            self.logger.info(f'Waiting for incoming connections...')
            self.connection, client_address = self.sock.accept()
            #if self.tcp_timeout > 0:
            self.connection.settimeout(1)
            self.logger.info(f'TCP Client connected: {client_address}')
            self._tcp_open_event.set()
            while not self.conn_is_closed and self.connection:
                try:
                    if self.tcp_timeout > 0:
                        self.logger.debug(f'Waiting for TCP-Data... Timeout-Counter: {self._tcp_timeout_counter}s')
                    if self.connection:
                        data = self.connection.recv(self.tcp_buffer_size)
                        self.logger.debug(f'TCP Data Received: {data}')
                        self._tcp_timeout_counter  = 0
                        if data:
                            if self.web_socket_client.is_ws_available():
                                self.logger.debug(f'Sent Data to WebSocket...')
                                self.web_socket_client.web_socket.sock.send_binary(
                                    data)
                        else:
                            break
                    else:
                        break
                except socket.timeout:
                    #self.web_socket_client.reconnect()
                    if self.tcp_timeout > 0 and self._tcp_timeout_counter >= self.tcp_timeout:
                        self.logger.debug(
                            f'TCP Timeout {self.tcp_timeout} reached!')
                        break
                    else:
                        self._tcp_timeout_counter += 1
                        continue

                except Exception as ex:
                    self.logger.debug(f'Type of TCP Error {type(ex)}')
                    self.logger.error(ex)
                    break
            # Restart the TCP Server
            if not self.script_mode:
                self._restart()
        except Exception as ex:
            self.logger.error(ex)

    def _start_server(self):
        self.logger.info(
            f'Starting TCP Server on localhost and port {self.port} ... ')
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = ('localhost', self.port)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(server_address)
        self.logger.info(
            f'TCP Server on localhost and port {self.port} successfully started.')

    def _restart(self):
        self.logger.info(
            f'Restarting TCP Connection...')
        self.stop_connection()
        #self.stop()
        if self.web_socket_client.is_ws_available():
            #self._start_server()
            self._start_connection()

    def is_tcp_socket_connected(self):
        if self.connection:
            return True
        tcp_result = self._tcp_open_event.wait()
        return tcp_result

    def is_tcp_socket_available(self):
        tcp_result = self._tcp_open_event.is_set()
        return tcp_result

    def stop_connection(self):
        # Close Client connection...
        if self.connection and not self.conn_is_closed:
            self.logger.info(
                f'Stopping TCP Connection {self.connection.getpeername()}')
            self.connection.close()
            # self.connection.shutdown(socket.SHUT_RDWR)
            self.connection = None
            self.conn_is_closed = True

    def stop(self):
        self.logger.info(f'Shutting down TCP Server...')
        self.stop_connection()
        if self.sock:
            # self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        self.logger.info(f'TCP Server shutdown successful!')
        # sys.exit()
