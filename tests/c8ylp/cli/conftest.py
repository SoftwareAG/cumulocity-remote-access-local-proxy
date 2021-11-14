"""SSH command tests"""
from unittest.mock import Mock, patch

import pytest
from c8ylp.rest_client.c8yclient import CumulocityClient
from tests.env import Environment
from tests.fixtures import FixtureCumulocityAPI


@pytest.fixture(name="c8yclient")
def fixture_c8yclient():
    """Cumulocity client fixture"""
    dummy_client = CumulocityClient("https://example.c8y.io")

    def set_tenant():
        dummy_client.tenant = "t12345"
        return dummy_client.tenant

    dummy_client.validate_tenant_id = Mock(side_effect=set_tenant)

    with patch("c8ylp.main.CumulocityClient", return_value=dummy_client) as mock_client:
        yield mock_client


@pytest.fixture(name="env")
def fixture_env():
    """Environment fixture"""
    yield Environment()


@pytest.fixture(name="c8yserver")
def fixture_c8yserver():
    """Cumulocity server fixture to simulate server responses"""
    api = FixtureCumulocityAPI()
    yield api
