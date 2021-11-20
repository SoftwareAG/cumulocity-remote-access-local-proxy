"""plugin command"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import click

from c8ylp import __ROOT_DIR__
from .. import options
from .core import ExitCodes, ProxyContext


plugin_folders = [
    Path(__ROOT_DIR__) / "plugins",
    (Path("~") / ".c8ylp" / "plugins"),
]


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

        plugin_args = [script_path, *additional_args]
        try:
            exit_code = subprocess.call(plugin_args, env=os.environ)
        except Exception as ex:
            proxy.show_error(
                "Failed to execute plugin. Did you set a shebang in the first line?. "
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

        for plugin_folder in plugin_folders:
            click.echo(f"Checking plugin folder: {plugin_folder}")
            plugin_folder = plugin_folder.expanduser()
            if plugin_folder.exists():
                for filename in os.listdir(str(plugin_folder)):
                    if filename.endswith(".py") and filename != "__init__.py":
                        cmds.append(filename[:-3])
                    elif filename.endswith(".sh"):
                        cmds.append(filename[:-3])

        cmds.sort()

        logging.debug("Detected plugins: %s", cmds)
        return cmds

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

        file_exts = [".py", ".sh"]

        plugins = []
        for plugin_folder in plugin_folders:
            plugin_folder = plugin_folder.expanduser()

            for ext in file_exts:
                path = plugin_folder.joinpath(cmd_name + ext)
                if os.path.exists(path):
                    plugins.append(path)

        if not plugins:
            logging.warning("Could not find plugin. name=%s", cmd_name)
            ctx.exit(ExitCodes.PLUGIN_NOT_FOUND)

        if cmd_name:
            logging.info("plugin found: name=%s, path=%s", cmd_name, plugins)

        for path in plugins:
            if path.suffix == ".py":
                logging.debug("Detected python script: %s", path)
                try:
                    namespace = load_python_plugin(path)
                except Exception as ex:
                    logging.warning("Failed to load python plugin. error=%s", ex)
                    ctx.exit(ExitCodes.PLUGIN_INVALID_FORMAT)
                break

            if path.suffix == ".sh":
                namespace["cli"] = create_bash_plugin(path)
                break

        if "cli" not in namespace:
            if cmd_name != ctx.parent.command.name:
                logging.warning(
                    "Plugin is missing a function called 'cli'. %s, parent=%s",
                    cmd_name,
                    ctx.parent.command.name,
                )
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
        c8ylp plugin copyto device01 <src> <dst>
    """
