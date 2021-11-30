#
# Copyright (c) 2021 Software AG, Darmstadt, Germany and/or its licensors
#
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""plugin command"""

import re
import os
import subprocess
import logging
import platform
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import click

from c8ylp import __ROOT_DIR__
from .. import options
from .core import ExitCodes, ProxyContext


def plugin_folders() -> List[Path]:
    """Plugin folders

    Returns:
        List[Path]: List of paths to search for plugins in
    """
    paths = [
        Path(__ROOT_DIR__) / "plugins",
    ]

    # optional add custom plugins location
    user_path = os.getenv("C8YLP_PLUGINS", "~/.c8ylp/plugins")
    if user_path:
        for path in user_path.split(";"):
            if path:
                paths.append(Path(path))

    return paths


def load_python_plugin(path: str) -> Dict[Any, Any]:
    """Load a python plugin from a file

    Args:
        path (str): Path

    Returns:
        Dict[Any, Any]: Namespace of the evaluated python file
    """
    namespace = {}
    with open(path) as file:
        code = compile(file.read(), str(path), "exec")
        # Eval is required to make a dynamic plugin
        # pylint: disable=eval-used
        eval(code, namespace, namespace)
    return namespace


def format_wsl_path(path: str) -> str:
    """Format windows path to the WSL equivalent

    Args:
        path (str): Windows path to convert

    Returns:
        str: WSL path, i.e. /mnt/c/my/path.sh
    """
    out_path = path.replace("\\", "/", -1)

    if re.search("^[a-z]:/", out_path, re.IGNORECASE):
        drive, _, rest = out_path.partition(":")
        out_path = f"/mnt/{drive.lower()}{rest}"

    return out_path


def build_cmd_args(cmd_args: List[str]) -> List[str]:
    """Build the command arguments to launch the plugin

    It allows for setting a custom shell via C8YLP_SHELL environment
    variable.

    Windows has special handling due to WSL and shell scripts not being
    executable by default.

    Args:
        cmd_args (List[str]): List of command arguments (without the shell)

    Returns:
        List[str]: Command arguments to execute specific to the OS

    """
    custom_shell = os.getenv("C8YLP_SHELL")
    out_args = [*cmd_args]

    if platform.system() != "Windows":
        if not custom_shell:
            # Rely on the script's shebang
            return out_args

        if not shutil.which(custom_shell):
            raise Exception(f"Could not find {custom_shell}")

        return [shutil.which(custom_shell)] + out_args

    #
    # Windows is more tricky as it does not read the bash shebang
    # so we have to help it out, but also being WSL friendly
    #
    shell = custom_shell or "bash"
    if not shutil.which(shell):
        # Let windows take care about executing the
        # default app associated
        return ["cmd.exe", "/c"] + out_args

    shell = [shutil.which(shell)]

    if (
        "wsl".casefold() in shell[0].casefold()
        or "\\windows\\system32\\bash.exe".casefold() in shell[0].casefold()
    ):
        #
        # WSL is going to be used, therefore the path needs to be reformatted
        # otherwise the path will not be found due to windows/linux differences
        # i.e. "C:\my\script\plugin.sh" => "/mnt/c/script/plugin.sh"
        out_args[0] = format_wsl_path(out_args[0])

    return shell + out_args


def create_bash_plugin(script_path: str) -> click.Command:
    """Create bash plugin wrapped in a click.Command

    Args:
        script_path (str): Path to the bash script

    Returns:
        click.Command: Command
    """

    @click.command()
    @options.common_options
    @click.argument(
        "additional_args",
        metavar="[ARGS]...",
        nargs=-1,
        type=click.UNPROCESSED,
    )
    @click.pass_context
    def bash_wrapper(wctx, additional_args, **kwargs):
        proxy = ProxyContext(wctx, kwargs).start_background()
        proxy.set_env()

        plugin_args = build_cmd_args([script_path, *additional_args])
        proxy.show_message(f"Running plugin: {' '.join(plugin_args)}")
        try:
            exit_code = subprocess.call(plugin_args, env=os.environ)
        except Exception as ex:
            proxy.show_error(
                "Failed to execute plugin. Is the plugin executable and contain a shebang on the first line?. "
                f"plugin={script_path}, error={ex}"
            )
            exit_code = ExitCodes.PLUGIN_EXECUTION_ERROR
        wctx.exit(exit_code)

    return bash_wrapper


class PluginCLI(click.MultiCommand):
    """Plugin CLI Command which can automatically discover plugins at runtime"""

    def list_commands(self, ctx: click.Context) -> List[str]:
        """List commands

        Args:
            ctx (click.Context): Click context

        Returns:
            List[str]: List of sub commands
        """
        cmds = []

        for plugin_folder in plugin_folders():
            click.echo(f"Checking plugin folder: {plugin_folder}")
            plugin_folder = plugin_folder.expanduser()
            if plugin_folder.exists():
                for filename in os.listdir(str(plugin_folder)):
                    if filename.endswith(".py") and filename != "__init__.py":
                        cmds.append(filename[:-3])
                    elif filename.endswith(".sh"):
                        cmds.append(filename[:-3])

        cmds.sort()

        logging.info("Detected plugins: %s", cmds)
        return cmds

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        """Get a command via its name. It will dynamically execute the
        plugin (if it is a python plugin) or wrap it in a click command
        if it is a bash plugin.

        When resilient parsing is activated (mostly during tab completion), then don't
        trigger an exit as it can affect the completion results from being displayed.

        Args:
            ctx (Context): Click context
            name (str): Name of the command

        Returns:
            Optional[click.Command]: Resolved command
        """
        # pylint: disable=too-many-branches
        namespace = {}

        file_exts = [".py", ".sh"]

        plugins = []
        for plugin_folder in plugin_folders():
            plugin_folder = plugin_folder.expanduser()

            for ext in file_exts:
                path = plugin_folder.joinpath(cmd_name + ext)
                if os.path.exists(path):
                    plugins.append(path)

        if not plugins:
            if ctx.resilient_parsing:
                return None
            logging.warning("Could not find plugin. name=%s", cmd_name)
            ctx.exit(ExitCodes.PLUGIN_NOT_FOUND)

        if cmd_name:
            logging.info("plugin found: name=%s, path=%s", cmd_name, plugins)

        for path in plugins:
            if path.suffix == ".py":
                logging.debug("Detected python script: %s", path)
                try:
                    namespace = load_python_plugin(str(path))
                except Exception as ex:
                    logging.warning("Failed to load python plugin. error=%s", ex)
                    if not ctx.resilient_parsing:
                        ctx.exit(ExitCodes.PLUGIN_INVALID_FORMAT)

                break

            if path.suffix == ".sh":
                namespace["cli"] = create_bash_plugin(str(path))
                break

        if "cli" not in namespace:
            if cmd_name != ctx.parent.command.name:
                logging.warning(
                    "Plugin is missing a function called 'cli'. %s, parent=%s",
                    cmd_name,
                    ctx.parent.command.name,
                )
                if ctx.resilient_parsing:
                    return None
                ctx.exit(ExitCodes.PLUGIN_INVALID_FORMAT)

        return namespace.get("cli")


@click.group()
@options.LOGGING_VERBOSE
def cli_plugin():
    """Plugins"""


@cli_plugin.command(
    "plugin",
    cls=PluginCLI,
    hidden=False,
    options_metavar="",
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
def run():
    """
    Run a custom plugin (installed under ~/.c8ylp/plugins/)

    Example 1:

    \b
        c8ylp plugin command device01 -- ssh -p \\$PORT myuser@localhost
    """
