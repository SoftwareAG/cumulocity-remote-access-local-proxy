"""Provides cli helpers that can be used for usage with the local proxy in scripts.

CLI Examples

#> python3 -m c8ylp.helper port
Get unused port number

#> python3 -m c8ylp.helper wait <port> <timeout_sec>
Wait for the given port to be opened
"""
import time
import sys
import socket
from contextlib import contextmanager


@contextmanager
def socketcontext(*args, **kw):
    """Socket context to ensure the socket is closed automatically when leaving the context"""
    sock = socket.socket(*args, **kw)
    try:
        yield sock
    finally:
        sock.close()


def wait_for_port(port: int, timeout: float = 30.0) -> None:
    """Wait for a port to be opened

    Args:
        port (int): Port number
        timeout (float): Timeout in seconds. Defaults to 30.0

    Raises:
        TimeoutError: Timeout error when the timeout period is exceeded
    """
    start_at = time.monotonic()
    expires_at = start_at + timeout
    while True:
        if is_port_open(port):
            duration = time.monotonic() - start_at
            print(f'Port is open. waited={duration:.2f}s')
            break

        if time.monotonic() >= expires_at:
            raise TimeoutError(f'Timed out waiting for port to be opened. port={port}, timeout={timeout}')
        time.sleep(0.25)


def is_port_open(port: int) -> bool:
    """Check if a port is open or not

    Args:
        port (int): Port number

    Returns:
        bool: True if the port is open
    """
    with socketcontext() as sock:
        try:
            sock.bind(('', port))
        except OSError  as ex:
            # port already in use error
            if ex.errno == 98:
                return True

    return False


def get_unused_port() -> int:
    """Get a port which is currently unused
    """
    with socketcontext() as sock:
        sock.bind(('', 0))
        return sock.getsockname()[1]


def show_usage() -> None:
    print("""
Usage:

    python3 -m c8ylp.helper <port|wait> [...options]

Examples:

    #> python3 -m c8ylp.helper port
    # Get unused port

    #> python3 -m c8ylp.helper wait <port> <timeout_sec>
    # Wait for a port to be open
        """)


if __name__ == '__main__':
    """Main cli intervace to
    """
    if len(sys.argv) > 1:
        subcommand = sys.argv[1]
    
    if '--help' in sys.argv or '-h' in sys.argv:
        show_usage()
        sys.exit(0)

    if subcommand.lower() == 'port':
        print(get_unused_port())
    elif subcommand.lower() == 'wait':
        port = 2222
        timeout = 30.0

        if len(sys.argv) > 2:
            port = int(sys.argv[2])

        if len(sys.argv) > 3:
            timeout = float(sys.argv[3])

        try:
            wait_for_port(port, timeout)
            sys.exit(0)
        except TimeoutError as ex:
            print(ex)
            sys.exit(1)
    else:
        print('Error: Unknown command')
        show_usage()
        sys.exit(2)
