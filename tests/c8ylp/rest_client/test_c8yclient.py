"""Cumulocity client tests"""

from c8ylp.rest_client.c8yclient import CumulocityClient


def test_client_defaults_to_https():
    """Test that client defaults to using https"""
    assert CumulocityClient("example.c8y.io").url == "https://example.c8y.io"
    assert CumulocityClient("https://example.c8y.io").url == "https://example.c8y.io"
    assert CumulocityClient("http://example.c8y.io").url == "http://example.c8y.io"
