
# Developer / Contribution Notes

## Project tasks

Project tasks can be run via the `invoke` command. But before the command can be used you need to install all the python dependencies.

To install the dependencies via pip, navigate to the project folder and execute:

```sh
pip3 install -r requirements.txt -r requirements-dev.txt
```

All of the project tasks are defined in the `tasks.py` file.

If you are running zsh you can activate tab completion definitions for the tasks by adding the following in your `~/.zshrc` or running it when starting a new zsh.

```sh
eval "$(invoke --print-completion-script=zsh)"
```

## Coding

The project uses normalized code formatting and linting to maintain a consistent coding styling.

Before submitting a Pull Request (PR), please run the following and fix any of the linting errors.

```sh
invoke format lint
```

All source files should also have a license header file. This can be added in automatically using the following task:

```sh
invoke add-license
```

Once executed commit the changes.

## Build

### Building Debian package (Ubuntu/Debian)

In order to build the Debian package (.deb) yourself first install the following dependencies:

```sh
sudo apt-get install -y python-all dh-python python3-stdeb
```

Then build the .deb file using:

```sh
invoke build_deb
```

You can then host the Debian package in an Debian repository so it can be installed via `apt`.

If you don't have a Debian repository available you can still install the .deb file manually by using:

```sh
sudo apt install /path/to/package/c8ylp.deb
```

Test if it installed successfully by entering `c8ylp` in the terminal.

## Testing

### Running unit tests

Execute all unit tests using:

```sh
invoke test
```

**Note**

The unit tests do not require Cumulocity credentials, as platform communication is mocked.

### Running Integration tests

Running the integration tests require a working proxy client/service running on a device. In addition, it requests working Cumulocity credentials.

Execute the integration tests by following the procedure below:

1. Create a dotenv file `.env` in the project root folder and add the following:

    ```sh
    #
    # User credentials
    #
    C8Y_HOST=
    C8Y_USER=
    C8Y_PASSWORD=

    #
    # Integration testing (where your Remote Access Device Proxy is running)
    #
    TEST_SSH_USER=<valid_device_username>
    TEST_DEVICE=<c8y_device_external_id>
    ```

2. Login to generate a valid token (i.e. after two-factor-authentication). The .env file will be updated automatically.

    ```sh
    python3 -m c8ylp login --env-file .env
    ```

3. Run the integration tests

    ```sh
    invoke test-integration
    ```

### Installing c8ylp from a specific branch

To install c8ylp from a development use the following command (replace `<branch>` with the name of your branch you want to install from.)

```sh
pip install git+https://github.com/SoftwareAG/cumulocity-remote-access-local-proxy.git@<branch>
```

## CLI Documentation

The CLI commands are also documented in the project in the form of markdown files (for online viewing). After changing any of the commands (or adding new ones), the documentation should be updated using the following:

```sh
inv generate-docs
```

## Publishing to pypi

The package can be published by running the following command. 

```sh
invoke publish
```

Though please note, the official publishing is handled by the Github actions.
