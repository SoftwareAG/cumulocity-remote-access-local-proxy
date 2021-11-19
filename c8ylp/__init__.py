"""c8ylp version"""
import os

from . import _version

__ROOT_DIR__ = os.path.dirname(os.path.abspath(__file__))  # This is your Project Root

__version__ = _version.get_versions()["version"]
