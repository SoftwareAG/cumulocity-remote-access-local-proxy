"""Test plugin shell handling"""

import pytest

from c8ylp.cli.plugin import format_wsl_path


@pytest.mark.parametrize(
    "path,expected",
    [
        ("c:\\myscript\\ to my\\plugin.sh", "/mnt/c/myscript/ to my/plugin.sh",),
        ("D:\\launcher.sh", "/mnt/d/launcher.sh",),
    ],
)
def test_format_wsl_path(
    path, expected
):
    """Test formating of a windows path to the WSL equivalent"""
    assert format_wsl_path(path) == expected
