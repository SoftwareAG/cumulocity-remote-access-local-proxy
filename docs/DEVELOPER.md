
## Project tasks

Project tasks can be run via the `invoke` command. But before the command is installed you need to install all the python dependencies by running:

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

The project uses normalized code formatting and linting to maintain a consistent code styling.

Before submitting a Pull Request, please run the following and fix any of the linting errors.

```sh
invoke format lint
```

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

Test if it is installed successfully by entering `c8ylp` in the terminal.

## Testing

### Running unit tests

Unit test can be run without 

```sh
invoke test
```

### Running Integration tests

Running the integration tests require a working client running on a device. So before the these tests can be run you need to add the following environment variables to the `.env` file.

1. Create a dotenv file `.env` in the project root folder and add the following:

    ```sh
    #
    # User credentials
    #
    C8Y_HOST=
    C8Y_USER=
    C8Y_PASSWORD=

    #
    # Integration testing
    #
    TEST_SSH_USER=<valid_device_username>
    TEST_DEVICE=<c8y_device_external_id>
    ```

2. Login to get generate a valid token (i.e. after two-factor-authentication). The .env file will be updated automatically.

    ```sh
    python3 -m c8ylp login --env-file .env
    ```

3. Run integration tests

    ```sh
    invoke test-integration
    ```

## CLI Documentation

The CLI commands are also documented in the project in the form of markdown files (for online viewing). After changing any of the commands (or adding new ones), the documentation can be updated using the following:

```sh
inv generate-docs 
```

## Publishing to pypi

The package can be published by running the following command. 

```sh
invoke publish
```

However normally the publishing is handled by the Github actions and does not need to be manually published.
