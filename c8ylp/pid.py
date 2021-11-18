"""PID Utilities"""

import os
import logging


def get_pid_file_text(device: str, url: str, config: str, user: str) -> str:
    """Format pid file text contents

    Args:
        device (str): Device external identity
        url (str): Cumulocity url
        config (str): Remote access type
        user (str): User

    Returns:
        str: Text contents that should be written to a pid file
    """
    pid = str(os.getpid())
    return f"{pid},{url},{device},{config},{user}"


def get_pid_from_line(line: str) -> int:
    """Get the process id from the contents of a pid file

    Args:
        line (str): Encoded PID information

    Returns:
        int: Porcess id
    """
    return int(str.split(line, ",")[0])


def upsert_pid_file(pidfile: str, device: str, url: str, config: str, user: str):
    """Create/update pid file

    Args:
        pidfile (str): PID file path
        device (str): Device external identity
        url (str): Cumulocity URL
        config (str): Remote access configuration type
        user (str): Cumulocity user
    """
    try:
        clean_pid_file(pidfile, os.getpid())
        pid_file_text = get_pid_file_text(device, url, config, user)
        logging.debug("Adding %s to PID-File %s", pid_file_text, pidfile)

        if not os.path.exists(pidfile):
            if not os.path.exists(os.path.dirname(pidfile)):
                os.makedirs(os.path.dirname(pidfile))

        with open(pid_file_text, "a+") as file:
            file.seek(0)
            file.write(pid_file_text)
            file.write("\n")

    except PermissionError:
        logging.error(
            "Could not write PID-File %s. Please create the folder manually and assign the correct permissions.",
            pidfile,
        )
        raise


def pid_is_active(pid: int) -> bool:
    """Check if a PID is active

    Args:
        pid (int): Process ID

    Returns:
        bool: True if the process is still running
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


def clean_pid_file(pidfile: str, pid: int):
    """Clean up pid file

    Args:
        pidfile (str): PID file path
        pid (int): current process id
    """
    if os.path.exists(pidfile):
        logging.debug("Cleaning Up PID %s in PID-File %s", pid, pidfile)
        pid = pid if pid is not None else os.getpid()
        with open(pidfile, "w+") as file:
            lines = file.readlines()
            file.seek(0)
            for line in lines:
                if get_pid_from_line(line) != pid:
                    file.write(line)
            file.truncate()

        if os.path.getsize(pidfile) == 0:
            os.remove(pidfile)


def kill_existing_instances(pidfile: str):
    """Kill existing instances of c8ylp

    Args:
        pidfile (str): PID file path
    """
    if os.path.exists(pidfile):
        with open(pidfile) as file:
            pid = int(os.getpid())
            for line in file:
                other_pid = get_pid_from_line(line)
                if pid != other_pid and pid_is_active(other_pid):
                    logging.info("Killing other running Process with PID %s", other_pid)
                    os.kill(get_pid_from_line(line), 9)
                clean_pid_file(pidfile, other_pid)
