"""plugin command"""

import os
import sys
import threading
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock
import click

from ..plugins import ssh
from c8ylp import __ROOT_DIR__
from c8ylp.helper import wait_for_port
from c8ylp.timer import CommandTimer
from .. import options
from .core import ProxyOptions, register_signals, run_proxy_in_background, start_proxy


plugin_folders = [
    Path(__ROOT_DIR__) / "plugins",
    (Path("~") / ".c8ylp" / "plugins").expanduser(),
]


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
        click.echo(f"Checking plugin folder: {str(plugin_folders)}")

        for plugin_folder in plugin_folders:
            if plugin_folder.exists():
                for filename in os.listdir(str(plugin_folder)):
                    if filename.endswith(".py") and filename != "__init__.py":
                        cmds.append(filename[:-3])
                    elif filename.endswith(".sh"):
                        cmds.append(filename[:-3])

        cmds.sort()

        logging.debug("Detected plugins: %s", cmds)
        return cmds

    # def get_command(self, ctx: Context, cmd_name: str) -> t.Optional[Command]:
    #     return super().get_command(ctx, cmd_name)

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        """Get a command via its name. It will dynamically execute the
        plugin (if it is a python plugin) or wrap it in a click command
        if it is a bash plugin.

        Args:
            ctx (Context): Click context
            name (str): Name of the command

        Returns:
            Optional[click.Command]: Resolved command
        """
        namespace = {}

        if cmd_name == "ssh":
            # namespace["cli"] = ssh.cli
            return ssh.cli

        file_exts = [".py", ".sh"]

        for plugin_folder in plugin_folders:
            for ext in file_exts:

                func = plugin_folder.joinpath(cmd_name + ext)
                if func.exists():
                    if ext == ".py":
                        logging.debug("Detected python script: %s", func)
                        if __ROOT_DIR__ in str(func):
                            pass
                        else:
                            with open(func) as file:
                                code = compile(file.read(), str(func), "exec")
                                # Eval is required to make a dynamic plugin
                                # pylint: disable=eval-used
                                eval(code, namespace, namespace)
                                break
                    elif ext == ".sh":
                        logging.debug("Detected bash script: %s", func)

                        def create_wrapper(script_path):
                            @click.command()
                            @click.pass_context
                            def bash_wrapper(wctx):
                                exit_code = subprocess.call(script_path, env=os.environ)
                                wctx.exit(exit_code)

                            return bash_wrapper

                        namespace["cli"] = create_wrapper(str(func))
                        break

        click.echo(f"plugin name: {cmd_name}")

        if "cli" not in namespace:
            logging.warning("Plugin is missing cli function. %s", namespace)
            return None

        return namespace["cli"]


@click.group()
def cli_plugin():
    """Plugins"""


@cli_plugin.command(
    "plugin",
    cls=PluginCLI,
    hidden=False,
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@options.ARG_DEVICE
@options.common_options
@click.pass_context
def run(ctx: click.Context, *_args, **kwargs):
    """
    Run a custom plugin (installed under ~/.c8ylp/plugins/)

    Example 1:
    \b
        c8ylp plugin device01 copyto <src> <dst>
    """
    ctx.obj["call"] = Mock

    click.echo("Running pre-install phase")
    opts = ProxyOptions().fromdict(kwargs)
    opts.script_mode = True
    run_proxy_in_background(ctx, opts)
