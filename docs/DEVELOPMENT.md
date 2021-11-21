
## Coding

The project uses normalized code formating and linting to maintain a consistent code styling.

Before submitting a Pull Request, please run the following and fix any of the linting errors.

```sh
invoke format lint
```

# Build

## Building debian package

In order to build the .deb yourself first install python-stdeb via apt. Afterwards run:

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
