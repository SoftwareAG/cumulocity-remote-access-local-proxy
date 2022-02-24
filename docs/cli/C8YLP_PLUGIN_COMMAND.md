
## c8ylp plugin command

```
Usage: c8ylp plugin command [OPTIONS] DEVICE [REMOTE_COMMANDS]...

  Start once-off proxy and execute a (local) script/command

          DEVICE is the device's external identity
          REMOTE_COMMANDS is the script or command to run after the proxy has been started

      All additional arguments will be passed to the script/command. Use "--"
      before     the additional arguments to prevent the arguments from being
      interpreted by     c8ylp (i.e. to avoid clashes with c8ylp).

  Available ENV variables (use single quotes to prevent expansion):

      DEVICE - external device identity
      PORT   - port number of the local proxy
      C8Y_HOST - Cumulocity host/url

  Example 1: Use scp to copy a file to a device

          c8ylp plugin command --env-file .env device01 \
              -- /usr/bin/scp -P '$PORT' myfile.tar.gz admin@localhost:/tmp

  Example 2: Run a custom script (not included) to copy a file from the device
  to the current folder

          c8ylp plugin command --env-file .env -v device01 ./copyfrom.sh /var/log/dpkg.log ./

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
  --env-file PATH                 Environment file to load. Any settings
                                  loaded via this file will control other
                                  options  [env var: C8YLP_ENV_FILE]
  --external-type TEXT            external Id Type  [env var:
                                  C8YLP_EXTERNAL_TYPE; default: c8y_Serial]
  -c, --config TEXT               name of the C8Y Remote Access Configuration
                                  [env var: C8YLP_CONFIG; default:
                                  Passthrough]
  --port INTEGER RANGE            TCP Port which should be opened. 0=Random
                                  port  [env var: C8YLP_PORT; default: 0;
                                  0<=x<=65535]
  --ping-interval INTEGER         Websocket ping interval in seconds.
                                  0=disabled  [env var: C8YLP_PING_INTERVAL;
                                  default: 0]
  --tcp-size INTEGER RANGE        TCP Package Size  [env var: C8YLP_TCP_SIZE;
                                  default: 4096; 1024<=x<=8290304]
  --tcp-timeout INTEGER           Timeout in sec. for inactivity. Can be
                                  activated with values > 0  [env var:
                                  C8YLP_TCP_TIMEOUT; default: 0]
  -v, --verbose                   Print Debug Information into the Logs and
                                  Console when set  [env var: C8YLP_VERBOSE]
  --ignore-ssl-validate           Ignore Validation for SSL Certificates while
                                  connecting to Websocket  [env var:
                                  C8YLP_IGNORE_SSL_VALIDATE]
  --store-token / --no-store-token
                                  Store the Cumulocity host, tenant and token
                                  to the env-file if a file is being used
                                  [env var: C8YLP_STORE_TOKEN]
  -d, --disable-prompts           [env var: C8YLP_DISABLE_PROMPTS]
  -h, --help                      Show this message and exit.

```
