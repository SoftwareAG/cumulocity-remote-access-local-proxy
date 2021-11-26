
# Migrating to v2

The following guide should help transitioning from version v1.x to v2.x.

## Option name changes

The following option names were changed:

|Old name|New name|
|--------|--------|
|--hostname|--host|
|--tfacode|--tfa-code|
|--extype|--external-type|
|--tcpsize|--tcp-size|
|--tcptimeout|--tcp-timeout|
|--scriptmode|(Removed)|
|--use-pid|(Removed)|
|--kill|(Removed)|


## Option change of behavior

The meaning of the following options were changed:

|Option|Old meaning|New meaning|
|---------|-----------|-----------|
|-h|Cumulocity host|Show command help|

## New Options

The following options were added:

|Option|Meaning|
|------|-------|
|--disable-prompts|Disable prompts|
|--store-token|Store the Cumulocity token into the specific dotenv file (--env-file). It can be disabled by setting the environment variable `C8YLP_STORE_TOKEN=false`|



## Configuration

Tired of having to managed the Cumulocity settings yourself? All commands accept a dotenv (environment file) which will load the configuration from file rather then reading it from the command line or prompting the user.

You can now generate a c8ylp environment file by using the following command.

```
c8ylp login --env-file .env
```

You will be prompted for all of the required information (if not already present in the given env file), then you can use the created file with `--env-file <file>` with other c8ylp commands.

Please note that your Cumulocity Password will not be stored in the environment file, however the token will be stored under the `C8Y_TOKEN` variable. The token will be reused (if it is still valid), otherwise the user will be prompted for their password and two-factor-authentication code again.

You can set your password inside the dotenv file by setting the `C8Y_PASSWORD` property, however it is not recommended for production environments.

Below is an example of an dotenv file:

```sh
C8Y_HOST=<cumulocity_host>
C8Y_USER=<your_cumulocity_username>
C8Y_PASSWORD=<optional_password>
```

`C8Y_TENANT` is not mandatory so it can be left out to reduce the number of required settings.

All of the options can also be set via environment variables and/or the dotenv file. Check out each command's help (by using `--help`) to see the corresponding environment variable's name.

### Server mode / non-script mode

If you were previously using `c8ylp` to start a local proxy in server mode (previously called non-script mode), then will have to change your command to:


```sh
# New way
c8ylp server


# Old way
c8ylp
```


### Connecting via ssh

If you were using c8ylp mainly to establish a ssh with a device (using the Passthrough feature of Cumulocity's Cloud Remote Access feature), then use the following subcommand:

```sh
c8ylp connect ssh <device_external_id> --env-file .env
```

This subcommand will start a once-off local proxy on a random (free) port, and then start an interactive ssh client. Once you ssh session exists, then the local proxy will shutdown. This makes it even more convenient to quickly connect to a device.

### Managing c8ylp instances

A PID file is no longer created when using server mode `c8ylp server`. This feature has been removed from c8ylp. It is now recommended that users use the `c8ylp connect ssh` or `c8ylp plugin command` which will automatically shutdown the local proxy after the user is finished with it.

However if you need an overview of all local proxy instances running on a machine then you can use the following linux commands:

```sh
# List all running instances
pgrep -fa c8ylp

# Kill all instances gracefully (SIGINT)
pkill -2 c8ylp

# Kill all instances forcefully (SIGKILL)
pkill -9 c8ylp
```