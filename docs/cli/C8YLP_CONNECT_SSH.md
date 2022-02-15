
## c8ylp connect ssh

```
Usage: c8ylp connect ssh [OPTIONS] DEVICE [REMOTE_COMMANDS]...

  Start once-off proxy and connect via ssh

  An interactive ssh is opened if a remote command is not provided.

  Once the ssh session is closed, then the local proxy will be shutdown.

  Use "--" before the remote commands to prevent the arguments from being
  interpreted by c8ylp (i.e. to avoid clashes with c8ylp).

      DEVICE is the device's external identity

  Example 1: Start an interactive SSH connection

      c8ylp connect ssh device01 --env-file .env --ssh-user admin

  Example 2: Execute a command via SSH

      c8ylp connect ssh device01 --env-file .env --ssh-user admin -- systemctl status ssh

  Example 3: Execute a complex command via SSH (use quotes to ensure command
  is sent to the device)

      c8ylp connect ssh device01 --env-file .env --ssh-user admin -- "systemctl status ssh; dpkg --list | grep ssh"

Options:
  --host TEXT               Cumulocity Hostname  [required] [env var:
                            C8Y_HOST]
  -t, --tenant TEXT         Cumulocity tenant id  [env var: C8Y_TENANT]
  -u, --user TEXT           Cumulocity username  [env var: C8Y_USER,
                            C8Y_USERNAME]
  -t, --token TEXT          Cumulocity token  [env var: C8Y_TOKEN]
  -p, --password TEXT       Cumulocity password  [env var: C8Y_PASSWORD]
  --tfa-code TEXT           TFA Code. Required when the 'TFA enabled' is
                            enabled for a user  [env var: C8Y_TFA_CODE]
  --env-file PATH           Environment file to load. Any settings loaded via
                            this file will control other options  [env var:
                            C8YLP_ENV_FILE]
  --external-type TEXT      external Id Type  [env var: C8YLP_EXTERNAL_TYPE;
                            default: c8y_Serial]
  -c, --config TEXT         name of the C8Y Remote Access Configuration  [env
                            var: C8YLP_CONFIG; default: Passthrough]
  --port INTEGER RANGE      TCP Port which should be opened. 0=Random port
                            [env var: C8YLP_PORT; default: 0; 0<=x<=65535]
  --ping-interval INTEGER   Websocket ping interval in seconds. 0=disabled
                            [env var: C8YLP_PING_INTERVAL; default: 0]
  --tcp-size INTEGER RANGE  TCP Package Size  [env var: C8YLP_TCP_SIZE;
                            default: 4096; 1024<=x<=8290304]
  --tcp-timeout INTEGER     Timeout in sec. for inactivity. Can be activated
                            with values > 0  [env var: C8YLP_TCP_TIMEOUT;
                            default: 0]
  -v, --verbose             Print Debug Information into the Logs and Console
                            when set  [env var: C8YLP_VERBOSE]
  --ignore-ssl-validate     Ignore Validation for SSL Certificates while
                            connecting to Websocket  [env var:
                            C8YLP_IGNORE_SSL_VALIDATE]
  --store-token             Store the Cumulocity host, tenant and token to the
                            env-file if a file is being used  [env var:
                            C8YLP_STORE_TOKEN]
  -d, --disable-prompts     [env var: C8YLP_DISABLE_PROMPTS]
  --ssh-user TEXT           SSH username which is configured on the device
                            [required]
  -h, --help                Show this message and exit.

```
