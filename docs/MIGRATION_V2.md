
# Migrating v2

The following guide should help transitioning from version 1.x to v2.

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

The following options were added to.

|Option|Meaning|
|------|-------|
|--disable-prompts|Disable prompts|
|--store-token|Store the Cumulocity token into the specific env file (--env-file). It can be disabled by setting the environment variable `C8YLP_STORE_TOKEN=false`|



## Configuration

Tired of having to managed the Cumulocity settings yourself? Then all commands accept a dotnev (environment file) which will load the configuration from file rather reading it from the command line or prompting the user.

You can now generate a c8ylp environment file by using the following command.

```
c8ylp login --env-file .env
```

You will be prompted for all of the required information (if not already present in the given env file), then you can use the created file with `--env-file` with other c8ylp commands.

Please note that your Cumulocity Password will not be stored the environment file, however the token will be stored under `C8Y_TOKEN`. The token will be reused (if it is still valid), otherwise the user will be prompted for their password and two-factor-authentication code again.

You can set your password inside the env file by setting the `C8Y_PASSWORD` property, however it is not recommended for production environments.

Below is an example of an environment file:

```sh
C8Y_HOST=<cumulocity_host>
C8Y_USER=<your_cumulocity_username>
C8Y_PASSWORD=<optional_password>
```

`C8Y_TENANT` is not mandatory so it can be left out to reduce the number of required settings.

All of the parameters can also be set via environment variables and/or the environment file. Check out the command's help (by using `--help`) to see the corresponding environment variable name.

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

This subcommand will start a once-off local proxy on a randomized port, and then start an interactive ssh client. This makes it even more convenient to quickly connect to a device.
