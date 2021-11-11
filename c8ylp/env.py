"""Environment utilities"""

import os


def loadenv(path: str) -> None:
    """Load environment variables from file

    Lines are ignored if they match any of the following
     * Empty line (only whitespace)
     * Lines starts with "#"
     * Lines starts with ";"

    Values may contain references to other environment variables by
    using "$NAME" or "${NAME}" syntax.

    Values with single or double quotes will be stripped from the value.

    Below is an example of a dotenv file:
    >>>
    ENV1=MYVALUE
    CUSTOMER_NAME="$USER"

    # Literal values can be surrounded with single quotes.
    CUSTOMER_NAME='$USER'
    >>>

    Args:
        path (str): Dotenv file path
    """
    with open(path, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";"):
                continue

            key, _, value = line.partition("=")

            if value.startswith("'") and value.endswith("'"):
                # Strip single quote wrapping, and skip env expansion
                value = value.strip("'")
            elif value.startswith('"') and value.endswith('"'):
                # Strip surrounding quotes
                value = os.path.expandvars(value.strip('"'))
            else:
                value = os.path.expandvars(value)

            os.environ[key] = value
