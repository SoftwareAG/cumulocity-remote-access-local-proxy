"""Test sessions"""

import responses
from c8ylp.rest_client.sessions import BaseUrlSession


@responses.activate
def test_session_with_partial_urls():
    """Test expansion of partial urls when sending requests"""
    session = BaseUrlSession("example.c8y.io")

    responses.add(
        "GET",
        url="https://example.c8y.io/partial/url",
    )
    response = session.get("/partial/url")
    assert response.status_code == 200
    assert response.url == "https://example.c8y.io/partial/url"


@responses.activate
def test_session_with_full_url():
    """Test handling of full urls. The hostname should be left untouched"""
    session = BaseUrlSession("example.c8y.io")

    responses.add(
        "GET",
        url="https://someotherurl.com/hello",
    )
    response = session.get("https://someotherurl.com/hello")
    assert response.status_code == 200
    assert response.url == "https://someotherurl.com/hello"
