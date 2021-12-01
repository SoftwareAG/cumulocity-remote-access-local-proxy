#!/bin/bash

# add local pip to PATH
export PATH="/home/vscode/.local/bin:$PATH"

#
# zsh specific settings
#
if [ -n "$ZSH_VERSION" ]; then
    # load completions for invoke
    source <(invoke --print-completion-script zsh)

    # init zsh competion
    autoload -U compinit; compinit -i

    # Prettier custom prompt
    export PROMPT='%(?.%F{green}✓.%F{red}✗%?)%f %B%F{240}%1~%f%b %# '

    # load c8ylp completions (if command is already built)
    if command -v c8ylp > /dev/null; then
        eval "$(_C8YLP_COMPLETE=zsh_source c8ylp)"
    fi
fi

#
# bash specific settings
#
if [ -n "$BASH_VERSION" ]; then
    if [ -f /etc/profile.d/bash_completion.sh ]; then
        source /etc/profile.d/bash_completion.sh
    fi

    # load completions for invoke
    source <(invoke --print-completion-script bash)

    # load c8ylp completions (if command is already built)
    if command -v c8ylp > /dev/null; then
        eval "$(_C8YLP_COMPLETE=bash_source c8ylp)"
    fi
fi

#
# Import env variable (with expansion) from a dotenv file.
# Defaults to .env
#
loadenv () {
    envfile=${1:-".env"}
    if [ -f "$envfile" ]; then
        echo "Importing env: $envfile"

        # import dotenv
        export $(cat "$envfile" | sed 's/#.*//g'| xargs)

        # substitute any reference env
        # Note: Can't do this on the same line as envsubst looks in already
        # exposed env variable
        export $(echo $(cat "$envfile" | sed 's/#.*//g'| xargs) | envsubst)
    fi
}
