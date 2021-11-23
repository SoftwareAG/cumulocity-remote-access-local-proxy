# Local Proxy for Cumulocity Cloud Remote Access

This is a proxy implementation for the Cloud Remote Access feature of Cumulocity which allows to connect to devices using native TCP-based clients like ssh, vnc, rdp etc.

Main purpose of this proxy is to bridge all TCP packets via WebSocket. The local proxy is designed to run on clients where the native client software is installed.

![architecture](img/Remote_access_architecture.png)

The proxy is written in Python3.

# Installation

The Local Proxy will be either provided as a Python executable or packaged as Software Bundle.

## Dependencies

The Local Proxy depends on the following components which either needs to be installed via pip or via package manager like apt:

* [certifi](https://pypi.org/project/certifi/)
* [click](https://pypi.org/project/click/)
* [requests](https://pypi.org/project/requests/)
* [setuptools](https://pypi.org/project/setuptools/)
* [websocket_client](https://pypi.org/project/websocket_client/)

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

Navigate to the root folder of the project and run:

```console
pip install .
```

## Installation as a Software Bundle

The Local Proxy can be installed by the Debian/Ubuntu Package Manager (apt).
Make sure that the package is available in your configured repositories and execute

```
sudo apt install c8ylp
```

If you don't have a repo available but just the *.deb file you can install it locally with

```
sudo apt install /path/to/package/c8ylp.deb
```

Test if it is installed successfully by entering `c8ylp` in the terminal.

## TODO: Update required?: Required Permissions in PID-Mode only (linux only)

When using the `--use-pid` parameter the Local Proxy will try to create a PID file in <strong>/var/run/c8ylp</strong> folder. Before starting the Local Proxy with that parameter you must make sure that the user who executes it has write permissions for that folder. For example for the user "proxyuser" part of group "proxyuser" use the following commands before initially starting the Proxy:

```sh
# linux only
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

c8ylp supports different commands depending on your use case. The commands are organized in a multi-level command structure. The list of available commands and subcommands can be shown by using the --help option.

The command can be launched by either using the `c8ylp` binary or my calling the `c8ylp` module by python.

```sh
c8ylp

# or calling via python
python3 -m c8ylp
```

The available commands can be shown using:

```console
% c8ylp --help
Usage: c8ylp [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  connect  Connect to a device via different protocols
  login    Login and save token to an environment file
  plugin   Run a custom plugin (installed under ~/.c8ylp/plugins/)
  server   Start local proxy in server mode
  version  Show the c8ylp version number
```

### Launching as local proxy server

```sh
c8ylp server <device> --env-file .env
```

### Launching as local proxy server then launching an interactive ssh session

```sh
c8ylp connect ssh <device> --ssh-user <device_username> --env-file .env
```

### Command documentation

The command usage and all parameters can be viewed on the following pages:

* [c8ylp](docs/cli/C8YLP.md)
* [c8ylp login](docs/cli/C8YLP_LOGIN.md)
* [c8ylp server](docs/cli/C8YLP_SERVER.md)
* [c8ylp connect](docs/cli/C8YLP_CONNECT.md)
* [c8ylp connect ssh](docs/cli/C8YLP_CONNECT_SSH.md)
* [c8ylp plugin](docs/cli/C8YLP_PLUGIN.md)
* [c8ylp plugin command](docs/cli/C8YLP_PLUGIN_COMMAND.md)

### TODO: Configuration

* Environment variables
* Dot env file (set via `--env-file <file>`)

You can execute `c8ylp --help` to get help about the parameters and execution.

Example Usage: 

```console
c8ylp server test-device --env-file .env
```

Additional the parameters can be set by using Environment Variables (see column "Enviroment Variables in the table above)

> Please note that the Local Proxy will block the current terminal session. If you want to use it in background just use "&" and/or "nohup". As the relevant information will be stored in a log file as well you can forward the output to dev/null or to syslog if you want to do so.
>```
>c8ylp [params] > /dev/null 2>&1
>```

If no TCP Client is connected but Web Socket Connection is open it might get be terminated by a server timeout. The Local Proxy will automatically reestablish the connection in this case.

If a TCP Client has been connected and the Web Socket Connection gets terminated, the TCP Client Connection will be terminated which results in that the Local Proxy terminates and needs to be restarted manually.

## Auto completion / tab completion

c8ylp (version >= 2.0.0) supports auto completion for bash, zsh and fish shells.

To add the completion, you will need to add the correspnding line to your shell profile, and reload your shell afterwards.

**Note**

Completion is not currently supported in cygwin.

```sh
# bash (profile: ~/.bashrc)
eval "$(_C8YLP_COMPLETE=bash_source c8ylp)"

# zsh (profile: ~/.zshrc)
eval "$(_C8YLP_COMPLETE=zsh_source c8ylp)"

# fish (profile: ~/.config/fish/config.fish)
_C8YLP_COMPLETE=fish_source c8ylp | source
```

# Plugins

`c8ylp` can be extended by the use of plugins (either via python or bash script). Checkout the [plugins](docs/PLUGINS.md) page for information about how to create a plugin.

Plugins are loaded at runtime and can be listed by running the following command:

```console
c8ylp plugin
```


# Log

The logfile can be found in the following directory. 

  ```console
  ~/.c8ylp/
  ```

Where `~` is your user folder.

To increase the detail of log use the paramter `--verbose or -v`. If set, the log will be written on debug level.

All relevant information will be sent to the console AND to the log file. So when running in background you can just ignore the console output: 

```
c8ylp [params] > /dev/null 2>&1
```

Also of course you can forward the log output to any logserver / file of your choice.

_____________________
These tools are provided as-is and without warranty or support. They do not constitute part of the Software AG product suite. Users are free to use, fork and modify them, subject to the license agreement. While Software AG welcomes contributions, we cannot guarantee to include every contribution in the master project.

For more information you can Ask a Question in the [Tech Community Forums](https://tech.forums.softwareag.com/tag/Cumulocity-IoT).
