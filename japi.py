import click
import logging
import os
import requests
import sys

from typing import Any, Dict
from pprint import pprint

logger = logging.getLogger("jelastic.py")


class JelasticAPIException(Exception):
    pass


class JelasticAPI:
    def __init__(self, apiurl: str, apitoken: str):
        """
        Get all needed data to connect to a Jelastic API
        """
        self.apiurl = apiurl
        self.apidata = {"session": apitoken}
        self.logger = logging.getLogger("JelasticAPI")

    def _apicall(self, uri: str, method: str = "get", data: dict = {}) -> Dict:
        """
        Lowest-level API call: that's the method that talks over the network to the Jelastic API
        """
        # Make sure we have our session in
        self.logger.debug("_apicall {} {}, data:{}".format(method.upper(), uri, data))
        data.update(self.apidata)
        r = getattr(requests, method)(self.apiurl + uri, data)
        if r.status_code != requests.codes.ok:
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
        return response

    def get(self, uri: str, data: dict = {}) -> Dict:
        """
        Launch a GET to the Jelastic API
        """
        self.logger.info("GET {}, data:{}".format(uri, data))
        return self._apicall(uri, "get", data)

    def post(self, uri: str, data: dict = {}) -> Dict:
        """
        Launch a POST to the Jelastic API
        """
        self.logger.info("POST {}, data:{}".format(uri, data))
        return self._apicall(uri, "post", data)

    def test(self) -> Dict:
        """
        Test that the connection to the Jelastic API works.
        """
        return self.post("/users/account/rest/getuserinfo")

    def GetEnvs(self) -> Dict:
        """
        environment.Control.GetEnvs Jelastic API call
        """
        response = self.post("environment/control/rest/getenvs")
        return response["infos"]

    def RedeployContainersByGroup(
        self, envName: str, tag: str, nodeGroup: str = "cp"
    ) -> Dict:
        """
        environment.Control.RedeployContainersByGroup Jelastic API call
        """
        response = self.post(
            "/environment/control/rest/redeploycontainersbygroup",
            {"tag": tag, "nodeGroup": nodeGroup, "envName": envName},
        )
        return response["responses"]

    def CloneEnv(self, srcEnvName: str, dstEnvName: str) -> Dict:
        """
        environment.Control.CloneEnv Jelastic API call
        """
        return self.post(
            "/environment/control/rest/cloneenv", {"srcEnvName": srcenvName}
        )
