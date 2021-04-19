import logging
from typing import Dict

import httpx

from .exceptions import JelasticAPIException


class JelasticAPIConnector:
    def __init__(self, apiurl: str, apitoken: str):
        """
        Get all needed data to connect to a Jelastic API
        """
        self.apiurl = apiurl
        self.apitoken = apitoken
        self.apidata = {"session": apitoken}
        self.logger = logging.getLogger(self.__class__.__name__)
        # httpx client. Default to no timeouts, as the Jelastic API is _synchronous_.
        self.client = httpx.Client(timeout=None)

    def is_functional(self) -> bool:
        """
        Whether this was meaningfully instantiated
        """
        try:
            return len(self.apiurl) > 0 and len(self.apidata["session"]) > 0
        except (TypeError, AttributeError):
            return False

    def _apicall(self, uri: str, method: str = "get", data: dict = {}) -> Dict:
        """
        Lowest-level API call: that's the method that talks over the network to the Jelastic API
        """
        # Make sure we have our session in
        self.logger.debug("_apicall {} {}, data:{}".format(method.upper(), uri, data))
        data.update(self.apidata)
        r = self.client.request(
            method=method, url="{url}{uri}".format(url=self.apiurl, uri=uri), data=data
        )
        if r.status_code != httpx.codes.OK:
            raise JelasticAPIException(
                "{method} to {uri} failed with HTTP code {code}".format(
                    method=method, uri=uri, code=r.status_code
                )
            )

        response = r.json()
        if response["result"] != 0:
            raise JelasticAPIException(
                "{method} to {uri} returned non-zero result: {result}".format(
                    method=method, uri=uri, result=response
                )
            )
        self.logger.debug(" response : {}".format(response))
        return response

    def _(self, function: str, **kwargs) -> Dict:
        """
        Direct API call, converting function paths into URLs; allows:
            JelasticAPIConnector._('Environment.Control.GetEnvs')
        """
        self.logger.info("{fnc}({data})".format(fnc=function, data=kwargs))
        # Determine function endpoint from the two-dotted string
        uri_chunks = function.split(".")
        if len(uri_chunks) != 3:
            raise JelasticAPIException(
                "Function ({fnc}) doesn't match standard Jelastic function (Group.Class.Function)".format(
                    fnc=function
                )
            )
        uri = "{grp}/{cls}/REST/{fnc}".format(
            grp=uri_chunks[0], cls=uri_chunks[1], fnc=uri_chunks[2]
        ).lower()

        return self._apicall(uri=uri, method="post", data=kwargs)
