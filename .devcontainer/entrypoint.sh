#!/bin/bash

SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

if ! command -v c8ylp > /dev/null; then

    pip3 install "$SCRIPT_DIR/.."
fi

# reload shell (so the tab completion reloads)
$SHELL
