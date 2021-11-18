"""plugin class"""

import os
import subprocess
import logging
from pathlib import Path
from typing import List, Optional
import click

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
