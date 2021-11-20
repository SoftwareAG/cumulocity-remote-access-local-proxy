"""Integration test fixtures"""

import os
from .fixtures import Device, FileFactory
from c8ylp.env import loadenv

import pytest


@pytest.fixture
def c8ydevice():
    """Cumulocity integration test device fixture"""

    test_env = os.getenv("TEST_ENV_FILE", ".env")
    os.environ.setdefault("C8YLP_ENV_FILE", test_env)

    if os.path.exists(test_env):
        loadenv(test_env)

    yield Device(
        device=os.getenv("TEST_DEVICE", ""), ssh_user=os.getenv("TEST_SSH_USER", "")
    )


@pytest.fixture
def file_factory(tmpdir):
    """File factory fixture"""
    yield FileFactory(dir=tmpdir)
