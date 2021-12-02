# Plugins

c8ylp supports plugins which allows the user to customize the usage of the local proxy and to run custom commands after the local proxy has started.

Common parameters can be injected into the scripts so that the plugin plugin only needs to focus on the additional functionality that the plugin provides.

The following plugin types are supported:

* python plugin (`<plugin_name>.py`)
* script plugin (`<plugin_name>.sh`) - Requires a linux shell (i.e. bash/sh etc.)

## Plugin location

Plugins should be added to the following folder, and the command name is taken from the file name (without the extension).

By default the plugins are located in the following directory:

```sh
~/.c8ylp/plugins
```

However you can change this location by setting the `C8YLP_PLUGINS` environment variable.

i.e.

```sh
# bash/zsh
export C8YLP_PLUGINS="/usr/share/c8ylp/plugins"

# PowerShell (windows)
$env:C8YLP_PLUGINS = "C:\common\c8ylp\plugins"
```

**Note:** The plugin scripts should be located directory under the plugins folder and not a subfolder!

## Plugin runtime environement

When plugins are executed, c8ylp injects some environment variables into the process so that information about the running local proxy (i.e. device name and port) can be easily referenced.

The following environment variables are can be used inside the plugin.

|Environment Variable|Description|
|--------|-----------|
|DEVICE|Name of the device|
|PORT|Port used by the Local Proxy|
|C8Y_HOST|Cumulocity host name, useful for displaying in console messages|


# Plugin examples

## Python plugin

A python plugin can be created using the Python [click](https://click.palletsprojects.com/) package. This options provides the better user experience as `click` provides a rich interface such as user prompts, environment binding, help descriptions etc.

The following example show how to create a plugin which can be called using:

```sh
c8ylp plugin python_ssh
```

This example provides a custom way to launch an interactive ssh session using special business logic to automatically select the ssh user based on the name of the device.

Firstly create a blank file in the following location (create the folder if it does not already exist):

```sh
~/.c8ylp/plugins/python_ssh.py
```

Now open the created file in a text edit and paste the following:

```py
import os
import subprocess
import click
from c8ylp import options
from c8ylp.cli.core import ProxyContext

@click.command()
@options.common_options     # Inherit common c8ylp options
@click.pass_context
def cli(ctx, **kwargs):
    # Start local proxy (in background thread)
    proxy = ProxyContext(ctx, kwargs).start_background()

    # Custom logic to select a ssh user by
    # calculating it from the device name
    device = proxy.device
    device_family_type, _ , _ = device.partition("-")
    device_users_by_family = {
        "typeA": "device1_admin",
        "typeB": "device2_admin",
        "typeC": "device3_admin",
    }

    ssh_user = device_users_by_family.get(device_family_type, "default_admin")

    # create custom ssh command to run
    ssh_args = [
        "ssh",
        "-o",
        "ServerAliveInterval=120",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-p",
        str(proxy.used_port),
        f"{ssh_user}@localhost",
    ]

    click.echo("Starting ssh session using: " + " ".join(ssh_args))

    exit_code = subprocess.call(ssh_args, env=os.environ)
    if exit_code != 0:
        proxy.show_error(f"SSH exited with a non-zero exit code. code={exit_code}")
    ctx.exit(exit_code)
```

Then use the plugin by executing the following:

```sh
# show help
c8ylp plugin python_ssh --help

# Example usage to connect to device (mydevice)
c8ylp plugin python_ssh mydevice --env-file .env
```

**Notes**

* The main command function needs to be called `cli`
* An error will be thrown if there are syntax errors in the python plugin


## Script plugin (i.e. bash)

The following is the same example as the Python plugin but re-written using bash. While this example may be shorter, it does not add any nice user help/descriptions tha the python counterpart has.

**File:**   `~/.c8ylp/plugins/bash_ssh.sh`

```sh
#!/bin/bash

# Guess the device user based on the device name
case "$DEVICE" in
  typeA*)
    SSH_USER=device1_admin
    ;;

  typeB*)
    SSH_USER=device1_admin
    ;;

  typeC*)
    SSH_USER=device1_admin
    ;;

  *)
    SSH_USER=default_user
    ;;
esac

echo "Connecting to device ($DEVICE) on ($C8Y_HOST) - $SSH_USER@localhost (port $PORT)"

ssh \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -p "$PORT" \
    "$SSH_USER@localhost"
```

Make the script executable

```sh
chmod +x ~/.c8ylp/plugins/bash_ssh.sh
```

Then use the plugin by executing the following:

```sh
# show help
c8ylp plugin bash_ssh --help

# Example usage to connect to device (mydevice)
c8ylp plugin bash_ssh mydevice --env-file .env
```

**Notes**

* The script must begin with a shebang, i.e. `#!/bin/bash`
* The script needs to be executable, otherwise a permission denied error will be returned
