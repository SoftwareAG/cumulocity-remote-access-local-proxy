#!/bin/bash

# add local pip to PATH
set -gx PATH "/home/vscode/.local/bin:$PATH"

#
# fish specific settings
#
invoke --print-completion-script fish | source

_C8YLP_COMPLETE=fish_source c8ylp | source

# custom prompt to show last exit code
function fish_prompt
    if test $status != 0
        # show cross
        set_color red
        echo -n \U2717"$status "
    else
        # show checkmark
        set_color green
        echo -n \U2713" "
    end
    set_color $fish_color_cwd
    echo -n (basename $PWD) "> "
    set_color normal
end
