
## c8ylp server

```
Validating c8y token: OK
Usage: c8ylp server [OPTIONS] DEVICE

  Start local proxy in server mode

      DEVICE is the device's external identity

  Once the local proxy has started, clients such as ssh and scp can be used to
  establish a connection to the device.

  Example 1: Start the local proxy, prompt for credentials (if not set via env variables)

          c8ylp server device01 --host https://example.c8y.io

  Example 2: Start the local proxy using environment file

          c8ylp server --env-file .env device01

  Example 3: Start the local proxy with randomized port

          c8ylp server --env-file .env --port 0 device01

Options:
  --host TEXT              Cumulocity Hostname  [required]
  -t, --tenant TEXT        Cumulocity tenant id  [env var: C8Y_TENANT]
  -u, --user TEXT          Cumulocity username  [env var: C8Y_USER,
                           C8Y_USERNAME]
  -t, --token TEXT         Cumulocity token  [env var: C8Y_TOKEN]
  -p, --password TEXT      Cumulocity password  [env var: C8Y_PASSWORD]
  --tfa-code TEXT          TFA Code. Required when the 'TFA enabled' is
                           enabled for a user  [env var: C8Y_TFA_CODE]
  --env-file PATH          Environment file to load. Any settings loaded via
                           this file will control other parameters
  --external-type TEXT     external Id Type  [env var: C8YLP_EXTERNAL_TYPE;
                           default: c8y_Serial]
  -c, --config TEXT        name of the C8Y Remote Access Configuration  [env
                           var: C8YLP_CONFIG; default: Passthrough]
  --port INTEGER RANGE     TCP Port which should be opened. 0=Random port
                           [env var: C8YLP_PORT; default: 0; 0<=x<=65535]
  --ping-interval INTEGER  Websocket ping interval in seconds. 0=disabled
                           [env var: C8YLP_PING_INTERVAL; default: 0]
  --tcp-size INTEGER       TCP Package Size  [env var: C8YLP_TCP_SIZE;
                           default: 4096]
  --tcp-timeout INTEGER    Timeout in sec. for inactivity. Can be activited
                           with values > 0  [env var: C8YLP_TCP_TIMEOUT;
                           default: 0]
  -v, --verbose            Print Debug Information into the Logs and Console
                           when set
  --ignore-ssl-validate    Ignore Validation for SSL Certificates while
                           connecting to Websocket
  --store-token            Store the Cumulocity host, tenant and token to the
                           env-file if a file is being used
  -d, --disable-prompts
  --reconnects INTEGER     number of reconnects to the Cloud Remote Service. 0
                           for infinite reconnects  [env var:
                           C8YLP_RECONNECTS; default: 5]
  -k, --kill TEXT          Kills all existing processes of c8ylp  [env var:
                           C8YLP_KILL]
  --use-pid                Will create a PID-File to store all Processes
                           currently running (see --pidfile for the location)
  --pid-file TEXT          PID-File file location to store all Processes
                           currently running  [env var: C8YLP_PID_FILE;
                           default: (dynamic)]
  -h, --help               Show this message and exit.

```