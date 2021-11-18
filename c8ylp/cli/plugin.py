"""plugin command"""

import os
import sys
import threading
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
import click

from c8ylp.helper import wait_for_port
from .. import options
from .core import ProxyOptions, register_signals, start_proxy


plugin_folder = (Path("~") / ".c8ylp" / "plugins").expanduser()


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
        click.echo(f"Checking plugin folder: {str(plugin_folder)}")

        if plugin_folder.expanduser().exists():
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

        file_exts = [".py", ".sh"]

        for ext in file_exts:
            func = os.path.join(plugin_folder, cmd_name + ext)
            if os.path.exists(func):
                if ext == ".py":
                    logging.debug("Detected python script: %s", func)
                    with open(func) as file:
                        code = compile(file.read(), func, "exec")
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

                    namespace["cli"] = create_wrapper(func)
                    break

        if "cli" not in namespace:
            logging.warning("Plugin is missing cli function. %s", namespace)
            return None

        return namespace["cli"]


@click.group()
def plugin():
    """Plugins"""


@plugin.command(
    "plugin",
    cls=PluginCLI,
    hidden=True,  # Hide for now ;)
    context_settings=dict(
        ignore_unknown_options=True,
    ),
)
@options.ARG_DEVICE
@options.HOSTNAME
@options.EXTERNAL_IDENTITY_TYPE
@options.REMOTE_ACCESS_TYPE
@options.C8Y_TENANT
@options.C8Y_USER
@options.C8Y_TOKEN
@options.C8Y_PASSWORD
@options.C8Y_TFA_CODE
@options.PORT_DEFAULT_RANDOM
@options.PING_INTERVAL
@options.TCP_SIZE
@options.TCP_TIMEOUT
@options.LOGGING_VERBOSE
@options.SSL_IGNORE_VERIFY
@options.ENV_FILE
@options.STORE_TOKEN
@options.DISABLE_PROMPT
@click.pass_context
def run(ctx: click.Context, *_args, **kwargs):
    """
    Run a custom plugin (installed under ~/.c8ylp/plugins/)

    Example 1:
    \b
        c8ylp plugin device01 copyto <src> <dst>
    """

    click.echo("Running pre-install phase")
    opts = ProxyOptions().fromdict(kwargs)
    opts.script_mode = True

    # Skip starting server if the user just want to see the help
    if "--help" in sys.argv or "-h" in sys.argv:
        return

    stop_signal = threading.Event()
    opts.skip_exit = True

    # Inject custom env variables for use within the script
    os.environ["DEVICE"] = str(opts.device)
    os.environ["PORT"] = str(opts.port)

    # register signals as the proxy will be starting in a background thread
    # to enable the proxy to run as a subcommand
    register_signals()

    # Start the proxy in a background thread so the user can
    background = threading.Thread(
        target=start_proxy, args=(ctx, opts, stop_signal), daemon=True
    )
    background.start()

    # Shutdown the server once the plugin has been run
    @ctx.call_on_close
    def _shutdown_server_thread():
        stop_signal.set()
        background.join()

    # Block until the port is actually open
    wait_for_port(opts.port)

    # The subcommand is called after this
