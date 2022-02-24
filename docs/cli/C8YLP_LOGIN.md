
## c8ylp login

```
Usage: c8ylp login [OPTIONS]

  Login and save token to an environment file

  You will be prompted for all of the relevant information, i.e. host,
  username, password and TFA code (if required)

  Example 1: Create/update an env-file by trying to login into Cumulocity

      c8ylp login --env-file mytenant.env

Options:
  --host TEXT                     Cumulocity Hostname  [required] [env var:
                                  C8Y_HOST]
  -t, --tenant TEXT               Cumulocity tenant id  [env var: C8Y_TENANT]
  -u, --user TEXT                 Cumulocity username  [env var: C8Y_USER,
                                  C8Y_USERNAME]
  --token TEXT                    Cumulocity token  [env var: C8Y_TOKEN]
  -p, --password TEXT             Cumulocity password  [env var: C8Y_PASSWORD]
  --tfa-code TEXT                 TFA Code. Required when the 'TFA enabled' is
                                  enabled for a user  [env var: C8Y_TFA_CODE]
  -v, --verbose                   Print Debug Information into the Logs and
                                  Console when set  [env var: C8YLP_VERBOSE]
  --env-file PATH                 Environment file to load. Any settings
                                  loaded via this file will control other
                                  options  [env var: C8YLP_ENV_FILE]
  --store-token / --no-store-token
                                  Store the Cumulocity host, tenant and token
                                  to the env-file if a file is being used
                                  [env var: C8YLP_STORE_TOKEN]
  -d, --disable-prompts           [env var: C8YLP_DISABLE_PROMPTS]
  -h, --help                      Show this message and exit.

```
