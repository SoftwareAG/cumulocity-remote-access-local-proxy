"""Integration fixtures"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Device:
    device: str = ""
    ssh_user: str = ""


class FileFactory:
    """File factory to generate files with random content"""

    def __init__(self, dir: str) -> None:
        self._dir = Path(dir)

    @property
    def dir(self) -> Path:
        """Directory where the temp files are created"""
        return self._dir

    def create_file(self, name: str, size_mb: int = 10) -> Path:
        path = self._dir / name
        with open(path, "wb") as file:
            for i in range(0, size_mb * 1000):
                file.write(os.urandom(1024))

        return path
