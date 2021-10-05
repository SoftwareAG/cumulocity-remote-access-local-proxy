# Local Proxy for Cumulocity Cloud Remote Access
This is a proxy implementation for the Cloud Remote Access feature of Cumulocity which allows to connect to devices using native TCP-based clients like ssh, vnc, rdp etc.

Main purpose of this proxy is to bridge all TCP packets via WebSocket. The local proxy is designed to run on clients where the native client software is installed.

![architecture](img/Remote_access_architecture.png)

The proxy is written in Python3.

# Installation
The Local Proxy will be either provided as a Python executable or packaged as Software Bundle.

## Dependencies
The Local Proxy depends on the following components which either needs to be installed via pip or via package manager like apt:

* [websocket_client](https://pypi.org/project/websocket_client/)
* [requests](https://pypi.org/project/requests/)
* [setuptools](https://pypi.org/project/setuptools/)

### PIP
To install the dependencies via pip, navigate to the project folder and execute:
```console
pip install -r requirements.txt
```

### Package Manager
Just install the dependencies via apt
```console
sudo apt install python-requests python-websocket python-setuptools
```
## Installation from pypi via pip

```console
pip install c8ylp
```

## Installation from Source Code
Navigate to the root folder of the Local Proxy and run 
```console
pip install .
```
afterwards.

## Installation as a Software Bundle

The Local Proxy can be installed by the Package Manager.
Make sure that the package is available in your configured repositories and execute
```
sudo apt install c8ylp
```

If you don't have a repo available but just the *.deb file you can install it locally with
```
sudo apt install /path/to/package/c8ylp.deb
```

Test if it is installed successfully by entering `c8ylp` in the terminal.

## Required Permissions in PID-Mode only

When using the `--use-pid` parameter the Local Proxy will try to create a PID file in <strong>/var/run/c8ylp</strong> folder. Before starting the Local Proxy with that parameter you must make sure that the user who executes it has write permissions for that folder. For example for the user "proxyuser" part of group "proxyuser" use the following commands before initially starting the Proxy:

```
sudo mkdir /var/run/c8ylp
sudo chown -R proxyuser:proxyuser /var/run/c8ylp
```

Alternatively you can run the agent as "root" user so the folder and file will be created automatically.

# Usage

>The Local Proxy needs to be executed for each device tunnel you want to establish. 
>Multiple device tunnels per single Local Proxy Instance is currently not supported due to the limitation of the SSH Protocol.
>
>This also includes that the provided TCP Port should be not in use by other Proxies or Services.

In a terminal session execute:
```
c8ylp [params]

# or launching directly via python
python3 -m c8ylp.main
```
Available Parameter:

| Short  | Long          | Environemt Variables | Required | Description
| -------|:-------------:|:--------------------:|:--------:|:-----------        
| -h     | --hostname    | C8Y_HOST             | x        | The Cumulocity Hostname.
| -d     | --device      | C8Y_DEVICE           | x        | The Device Name (ext. Id of Cumulocity).
|        | --extype      | C8Y_EXTYPE           |          | The external Id Type. Default: "c8y_Serial"
| -c     | --config      | C8Y_CONFIG           |          | The name of the C8Y Remote Access Configuration. Default: "Passthrough"
| -t     | --tenant      | C8Y_TENANT           | x        | The tenant Id of Cumulocity
| -u     | --user        | C8Y_USER             | x        | The username of Cumulocity
| -p     | --password    | C8Y_PASSWORD         | x        | The password of Cumulocity
|        | --tfacode     |                      |          | The TFA Code when an user with the Option "TFA enabled" is used
|        | --port        | C8Y_PORT             |          | The TCP Port which should be opened. Default: 2222
| -k     | --kill        |                      |          | Kills all existing processes of c8ylp. Only availavle when 'use-pid' parameter is set.
|        | --tcpsize     | C8Y_TCPSIZE          |          | The TCP Package Size. Default: 32768
|        | --tcptimeout  | C8Y_TCPTIMEOUT       |          | Timeout in sec. for inactivity. Can be activited with values > 0. Default deactivated.
| -v     | --verbose     |                      |          | Print Debug Information into the Logs and Console when set.
| -s     | --scriptmode  |                      |          | Stops the TCP Server after first connection. No automatical restart! No WebSocket Reconnects!
|        |               | C8Y_TOKEN            |          | When set and valid no user, password, tenant, tfacode must be provided.
|        | --ignore-ssl-validate |              |          | Ignore Validation for SSL Certificates while connecting to Websocket.
|        | --use-pid     |                      |          | Will create a PID-File in /var/run/c8ylp to store all Processes currently running.
|        | --reconnects  |                      |          | The number of reconnects to the Cloud Remote Service. 0 for infinite reconnects, -1 for deactivation. Default: 5

You can execute `c8ylp --help` to get help about the parameters and execution.

Example Usage: 
```console
c8ylp  -h examples.cumulocity.com -d test-device -c "SSH Passthrough" -t t1111 -u admin -p verysecret
```

Additional the parameters can be set by using Environment Variables (see column "Enviroment Variables in the table above)

> Please note that the Local Proxy will block the current terminal session. If you want to use it in background just use "&" and/or "nohup". As the relevant information will be stored in a log file as well you can forward the output to dev/null or to syslog if you want to do so.
>```
>c8ylp [params] > /dev/null 2>&1
>```

If no TCP Client is connected but Web Socket Connection is open it might get be terminated by a server timeout. The Local Proxy will automatically reestablish the connection in this case.

If a TCP Client has been connected and the Web Socket Connection gets terminated, the TCP Client Connection will be terminated which results in that the Local Proxy terminates and needs to be restarted manually.


# Build

In order to build the .deb yourself first install python-stdeb via apt. Afterwards run:

    python3 setup.py --command-packages=stdeb.command bdist_deb

on the level of the setup.py.

# Log
The logfile can be found in the following directory. 

~ = Your user-folder.

    ~/.c8ylp/

To increase the detail of log use the paramter -v / --verbose. If set the log will be written on debug level.

All relevant information will be sent to the console AND to the log file. So when running in background you can just ignore the console output: 
```
c8ylp [params] > /dev/null 2>&1
```

Also of course you can forward the log output to any logserver / file of your choice.

_____________________
These tools are provided as-is and without warranty or support. They do not constitute part of the Software AG product suite. Users are free to use, fork and modify them, subject to the license agreement. While Software AG welcomes contributions, we cannot guarantee to include every contribution in the master project.

For more information you can Ask a Question in the [Tech Community Forums](https://tech.forums.softwareag.com/tag/Cumulocity-IoT).
