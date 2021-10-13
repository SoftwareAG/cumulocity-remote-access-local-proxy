#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import getopt
import logging
import os
import pathlib
import sys
import signal
import threading
from logging.handlers import RotatingFileHandler
from os.path import expanduser
import platform

from c8ylp.rest_client.c8yclient import CumulocityClient
from c8ylp.tcp_socket.tcp_server import TCPServer
from c8ylp.websocket_client.ws_client import WebsocketClient

PIDFILE = '/var/run/c8ylp/c8ylp'

class ExitCommand(Exception):
    pass

def signal_handler(signal, frame):
    raise ExitCommand()

def start():
    if platform.system() in ('Linux', 'Darwin'):
        signal.signal(signal.SIGUSR1, signal_handler)
    else:
        signal.signal(signal.SIGINT, signal_handler)
    home = expanduser('~')
    path = pathlib.Path(home + '/.c8ylp')
    loglevel = logging.INFO
    path.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(loglevel)
    log_file_formatter = logging.Formatter(
        '%(asctime)s %(threadName)s %(levelname)s %(name)s %(message)s')
    log_console_formatter = logging.Formatter('%(message)s')

    # Set default log format
    if len(logger.handlers) == 0:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_console_formatter)
        console_handler.setLevel(loglevel)
        logger.addHandler(console_handler)
    else:
        handler = logger.handlers[0]
        handler.setFormatter(log_console_formatter)

    # Max 5 log files each 10 MB.
    rotate_handler = RotatingFileHandler(filename=path / 'localproxy.log', maxBytes=10000000,
                                         backupCount=5)
    rotate_handler.setFormatter(log_file_formatter)
    rotate_handler.setLevel(loglevel)
    # Log to Rotating File
    logger.addHandler(rotate_handler)
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:d:c:t:u:p:kvs",
                                   ["help", "hostname=", "device=", "extype=", "config=", "tenant=", "username=",
                                    "password=", "tfacode=", "port=", "kill", "tcpsize=", "tcptimeout=", "verbose",
                                    "scriptmode",
                                    "ignore-ssl-validate", "use-pid", "reconnects="])
    except getopt.GetoptError as e:
        logging.error(e)
        help()

    logging.debug(f'OPTIONS: {opts}')
    # if len(opts) == 0:
    #    print(help())
    host = os.environ.get('C8Y_HOST')
    device = os.environ.get('C8Y_DEVICE')

    extype = os.environ.get('C8Y_EXTYPE') if os.environ.get('C8Y_EXTYPE') else 'c8y_Serial'
    config_name = os.environ.get('C8Y_CONFIG') if os.environ.get('C8Y_CONFIG') else 'Passthrough'
    tenant = os.environ.get('C8Y_TENANT')
    user = os.environ.get('C8Y_USER')
    password = os.environ.get('C8Y_PASSWORD')
    tcp_size = int(os.environ.get('C8Y_TCPSIZE')) if os.environ.get('C8Y_TCPSIZE', '').isnumeric() else 4096
    tcp_timeout = int(os.environ.get('C8Y_TCPTIMEOUT')) if os.environ.get('C8Y_TCPTIMEOUT', '').isnumeric() else 0
    port = int(os.environ.get('C8Y_PORT')) if os.environ.get('C8Y_PORT', '').isnumeric() else 2222
    ping_interval = int(os.environ.get('C8Y_PING_INTERVAL')) if os.environ.get('C8Y_PING_INTERVAL', '').isnumeric() else 0
    token = os.environ.get('C8Y_TOKEN')
    tfacode = None
    script_mode = False
    ignore_ssl_validate = False
    use_pid = False
    kill_instances = False
    reconnects = 5
    for option_key, option_value in opts:
        if option_key in ('-h', '--hostname'):
            host = option_value
        elif option_key in ('-d', '--device'):
            device = option_value
        elif option_key in '--extype':
            extype = option_value
        elif option_key in ('-c', '--config'):
            config_name = option_value
        elif option_key in ('-t', '--tenant'):
            tenant = option_value
        elif option_key in ('-u', '--username'):
            user = option_value
        elif option_key in ('-p', '--password'):
            password = option_value
        elif option_key in ['--tfacode']:
            tfacode = option_value
        elif option_key in ['--port']:
            port = int(option_value)
        elif option_key in ['-k', '--kill']:
            kill_instances = True
        elif option_key in ['--tcpsize']:
            tcp_size = int(option_value)
        elif option_key in ['--tcptimeout']:
            tcp_timeout = int(option_value)
        elif option_key in ['-v', '--verbose']:
            verbose_log()
        elif option_key in ['-s', '--scriptmode']:
            script_mode = True
        elif option_key in ['--ignore-ssl-validate']:
            ignore_ssl_validate = True
        elif option_key in ['--use-pid']:
            use_pid = True
        elif option_key in ['--reconnects']:
            reconnects = int(option_value)
        elif option_key in ['--help']:
            help()
    if script_mode:
        reconnects = -1
    validate_parameter(host, device, extype, config_name,
                       tenant, user, password, token)
    if use_pid:
        upsert_pid_file(device, host, config_name, user)
    if kill_instances:
        if use_pid:
            kill_existing_instances()
        else:
            logging.warn(f'WARNING: Killing existing instances is only supported when "--use-pid" is used.')
    client = CumulocityClient(host, tenant, user, password, tfacode, ignore_ssl_validate)
    tenant_id_valid = client.validate_tenant_id()
    if tenant_id_valid is not None:
        logging.warn(f'WARNING: Tenant ID {tenant} does not exist. Try using this Tenant ID {tenant_id_valid} next time!')
    session = None
    if token:
        client.validate_token()
    else:
        session = client.retrieve_token()
    mor = client.read_mo(device, extype)
    config_id = client.get_config_id(mor, config_name)
    device_id = client.get_device_id(mor)
    
    is_authorized = client.validate_remote_access_role()
    if not is_authorized:
        logging.error(f'User {user} is not authorized to use Cloud Remote Access. Contact your Cumulocity Admin!')
        sys.exit(1)

    client_opts = {
        'host': host,
        'tenant': tenant,
        'user': user,
        'password': password,
        'config_id': config_id,
        'device_id': device_id,
        'session': session,
        'token': token,
        'ignore_ssl_validate': ignore_ssl_validate,
        'reconnects': reconnects,
        'ping_interval': ping_interval,
    }
    websocket_client = WebsocketClient(**client_opts)
    wst = websocket_client.connect()
    tcp_server = TCPServer(port, websocket_client, tcp_size, tcp_timeout, wst, script_mode)
    # TCP is blocking...
    websocket_client.tcp_server = tcp_server
    try:
        tcp_server.start()
    except Exception as ex:
        logging.error(f'Error on TCP-Server {ex}')
    finally:
        if use_pid:
            clean_pid_file(None)
        tcp_server.stop()
        sys.exit(0)


def verbose_log():
    logging.info(f'Verbose logging activated.')
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        handler.setLevel(logging.DEBUG)


def upsert_pid_file(device, url, config, user):
    try:
        clean_pid_file(None)
        pid_file_text = get_pid_file_text(device, url, config, user)
        logging.debug(f'Adding {pid_file_text} to PID-File {PIDFILE}')
        if not os.path.exists(PIDFILE):
            if not os.path.exists(os.path.dirname(PIDFILE)):
                os.makedirs(os.path.dirname(PIDFILE))
            file = open(PIDFILE, 'w')
            file.seek(0)
        else:
            file = open(PIDFILE, 'a+')
            file.seek(0)
        file.write(pid_file_text)
        file.write('\n')
    except PermissionError:
        logging.error(
            f'Could not write PID-File {PIDFILE}. Please create the folder manually and assign the correct permissions.')
        sys.exit(1)


def get_pid_file_text(device, url, config, user):
    pid = str(os.getpid())
    return f'{pid},{url},{device},{config},{user}'


def get_pid_from_line(line):
    return int(str.split(line, ',')[0])


def pid_is_active(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def clean_pid_file(pid):
    if os.path.exists(PIDFILE):
        logging.debug(f'Cleaning Up PID {pid} in PID-File {PIDFILE}')
        pid = pid if pid is not None else os.getpid()
        with open(PIDFILE, "r+") as file:
            lines = file.readlines()
            file.seek(0)
            for line in lines:
                if get_pid_from_line(line) != pid:
                    file.write(line)
            file.truncate()
            if os.path.getsize(PIDFILE) == 0:
                os.remove(PIDFILE)


def kill_existing_instances():
    if os.path.exists(PIDFILE):
        file = open(PIDFILE)
        pid = int(os.getpid())
        #logging.info(f'Current PID {pid}')
        for line in file:
            other_pid = get_pid_from_line(line)
            if pid != other_pid and pid_is_active(other_pid):
                logging.info(
                    f'Killing other running Process with PID {other_pid}')
                os.kill(get_pid_from_line(line), 9)
            clean_pid_file(other_pid)


def validate_parameter(host, device, extpye, config_name, tenant, user, password, token):
    if not host:
        logging.error(f'Hostname is missing!')
        print('Mandatory parameter -h, --hostname is missing')
        print(_help_message())
        sys.exit(1)

    if not device:
        logging.error(f'Device Name is missing!')
        print('Mandatory parameter -d, --device is missing')
        print(_help_message())
        sys.exit(1)

    if not config_name:
        logging.error(f'Configuration Name is missing!')
        print('Mandatory parameter -c, --config is missing')
        print(_help_message())
        sys.exit(1)

    if not tenant and not token:
        logging.error(f'Tenant is missing!')
        print('Mandatory parameter -t, --tenant is missing')
        print(_help_message())
        sys.exit(1)

    if not user and not token:
        logging.error(f'User is missing!')
        print('Mandatory parameter -u, --user is missing')
        print(_help_message())
        sys.exit(1)

    if not password and not token:
        logging.error(f'Password is missing!')
        print('Mandatory parameter -p, --password is missing')
        print(_help_message())
        sys.exit(1)


def help():
    print(_help_message())
    sys.exit(2)


def _help_message() -> str:
    return str('Usage: c8ylp [params]\n'
               '\n'
               'Parameter:\n'
               ' --help                 show this help message and exit\n'
               ' -h, --hostname         REQUIRED, the Cumulocity Hostname\n'
               ' -d, --device           REQUIRED, the Device Name (ext. Id of Cumulocity)\n'
               ' --extype               OPTIONAL, the external Id Type. Default: "c8y_Serial"\n'
               ' -c, --config           OPTIONAL, the name of the C8Y Remote Access Configuration. Default: "Passthrough"\n'
               ' -t, --tenant           REQUIRED, the tenant Id of Cumulocity\n'
               ' -u, --user             REQUIRED, the username of Cumulocity\n'
               ' -p, --password         REQUIRED, the password of Cumulocity\n'
               ' --tfacode              OPTIONAL, the TFA Code when an user with the Option "TFA enabled" is used\n'
               ' --port                 OPTIONAL, the TCP Port which should be opened. Default: 2222\n'
               ' -k, --kill             OPTIONAL, kills all existing processes of c8ylp\n'
               ' --tcpsize              OPTIONAL, the TCP Package Size. Default: 32768\n'
               ' --tcptimeout           OPTIONAL, Timeout in sec. for inactivity. Can be activited with values > 0. Default: Deactivated\n'
               ' -v, --verbose          OPTIONAL, Print Debug Information into the Logs and Console when set.\n'
               ' -s, --scriptmode       OPTIONAL, Stops the TCP Server after first connection. No automatical restart!\n'
               ' --ignore-ssl-validate  OPTIONAL, Ignore Validation for SSL Certificates while connecting to Websocket'
               ' --use-pid              OPTIONAL, Will create a PID-File in /var/run/c8ylp to store all Processes currently running.\n'
               ' --reconnects           OPTIONAL, The number of reconnects to the Cloud Remote Service. 0 for infinite reconnects. Default: 5'
               '\n')


if __name__ == '__main__':
    start()
