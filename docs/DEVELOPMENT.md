
## Project tasks

Project tasks can be run via the `invoke` command. But before the command is installed you need to install all the python dependencies by running:

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

# Build

## Building debian package

In order to build the .deb yourself first install python3-stdeb via apt. Afterwards run:

    python3 setup.py --command-packages=stdeb.command bdist_deb

on the level of the setup.py.

## Testing

### Running unit tests

Unit test can be run without 

```sh
invoke test
```

### Running Integration tests

Running the integration test require a working client running on a device. So before the these tests can be run you need to add the following environment variables to the `.env` file.

1. Create a dotenv file `.env` in the project root folder and add the following:

    ```sh
    #
    # User credentials
    #
    C8Y_HOST=
    C8Y_TENANT=
    C8Y_TOKEN=
    C8Y_PASSWORD=
    C8Y_USER=

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

## Publishing to PyPi

The package can be published by running the following command. 

```
invoke publish
```

However normally the publishing is handled by the Github actions and does not need to be manually published.
