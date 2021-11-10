"""Custom request sessions"""

import logging
import requests


class BaseUrlSession(requests.Session):
    """Cumulocity requests session which automatically adds the given prefix
    to urls when sending the requests (if the url is not already fully defined)

    i.e. inventory/managedObjects => https://cumulocity.com/inventory/managedObjects

    References:
        * https://github.com/psf/requests/issues/2554
    """

    def __init__(self, prefix_url: str, reuse_session: bool = False):
        if not prefix_url.startswith("http"):
            # default to https!
            prefix_url = f"https://{prefix_url}"
        self.prefix_url = prefix_url
        self.reuse_session = reuse_session
        self.default_timeout = 30.0
        super().__init__()

    def expand_url(self, url: str) -> str:
        """Example the url if only a partial url (i.e /event/events) is given.

        Args:
            url (str): Partial or full url

        Returns:
            str: Returns full url (prepends the prefixUrl if a partial url is detected)
        """
        if not url.startswith("http"):
            url = self.prefix_url + "/" + url.lstrip("/")
        return url

    def request(self, method: str, url: str, *args, **kwargs) -> requests.Response:
        """Override default request method to automatically add the host to the url
        if the given url does not start with http

        Args:
            method (str): Request method (see requests.request for more details)
            url (str): Partial url (which will be joined with the prefix_url)
                       If it starts with http, then the prefix will not be prepended
            args: additional args passed to the requests method
            kwargs: additional args passed to the requests method

        Returns:
            requests.Response: Request response
        """

        # pylint: disable=arguments-differ
        url = self.expand_url(url)

        if self.reuse_session:
            send_kwargs = {
                "timeout": kwargs.pop("timeout", self.default_timeout),
                "proxies": kwargs.pop("proxies", self.proxies),
                "allow_redirects": kwargs.pop("allow_redirects", True),
                "stream": kwargs.pop("stream", self.stream),
                "verify": kwargs.pop("verify", self.verify),
                "cert": kwargs.pop("cert", self.cert),
            }

            prepped = super().prepare_request(
                requests.Request(method, url, *args, **kwargs)
            )
            logging.debug("Sending requests to %s", url)
            response = super().send(prepped, **send_kwargs)
            return response

        #
        # Use new session (to avoid read timeout errors due to stale connections)
        #

        # Extract send arguments
        send_kwargs = {
            "timeout": kwargs.pop("timeout", self.default_timeout),
            "proxies": kwargs.pop("proxies", self.proxies),
            "allow_redirects": kwargs.pop("allow_redirects", True),
            "stream": kwargs.pop("stream", self.stream),
            "verify": kwargs.pop("verify", self.verify),
            "cert": kwargs.pop("cert", self.cert),
        }

        # prepare request
        prep = super().prepare_request(
            requests.Request(method, url, *args, **kwargs)
        )

        logging.debug("Sending requests to %s", url)

        # Send the request
        with requests.Session() as session:
            return session.send(prep, **send_kwargs)
