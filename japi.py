import click
import json
import logging
import os
import requests
import sys

from typing import Any, Dict
from pprint import pprint

logger = logging.getLogger("jelastic.py")


class JelasticAPIException(Exception):
    pass


class JelasticAPIConnector:
    def __init__(self, apiurl: str, apitoken: str):
        """
        Get all needed data to connect to a Jelastic API
        """
        self.apiurl = apiurl
        self.apidata = {"session": apitoken}
        self.logger = logging.getLogger("JelasticAPIConnector")

    def _apicall(self, uri: str, method: str = "get", data: dict = {}) -> Dict:
        """
        Lowest-level API call: that's the method that talks over the network to the Jelastic API
        """
        # Make sure we have our session in
        self.logger.debug("_apicall {} {}, data:{}".format(method.upper(), uri, data))
        data.update(self.apidata)
        r = getattr(requests, method)(
            "{url}{uri}".format(url=self.apiurl, uri=uri), data
        )
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

    def _(self, function: str, **kwargs) -> Dict:
        """
        Direct API call, converting function paths into URLs; allows:
            JelasticAPI._('Environment.Control.GetEnvs')
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


class JelasticAPI:
    def __init__(self, apiurl: str, apitoken: str):
        """
        Get all needed data to connect to a Jelastic API
        """
        self.japic = JelasticAPIConnector(apiurl=apiurl, apitoken=apitoken)
        self.logger = logging.getLogger("JelasticAPI")

    def test(self) -> Dict:
        """
        Test that the connection to the Jelastic API works.
        """
        return self.japic._("Users.Account.GetUserInfo")

    def GetEnvs(self) -> Dict:
        """
        Environment.Control.GetEnvs Jelastic API call
        """
        response = self.japic._("Environment.Control.GetEnvs")
        return response["infos"]

    def GetEnvInfo(self, envName: str) -> Dict:
        """
        Environment.Control.GetEnvInfo Jelastic API call
        """
        return self.japic._("Environment.Control.GetEnvInfo", envName=envName)

    def RedeployContainersByGroup(
        self, envName: str, tag: str, nodeGroup: str = "cp"
    ) -> Dict:
        """
        Environment.Control.RedeployContainersByGroup Jelastic API call
        """
        response = self.japic._(
            "Environment.Control.RedeployContainersByGroup",
            tag=tag,
            nodeGroup=nodeGroup,
            envName=envName,
        )
        return response["responses"]

    def CloneEnv(self, srcEnvName: str, dstEnvName: str) -> Dict:
        """
        Environment.Control.CloneEnv Jelastic API call
        """
        return self.japic._(
            "Environment.Control.CloneEnv", srcEnvName=srcEnvName, dstEnvName=dstEnvName
        )

    def AddContainerEnvVars(
        self, envName: str, nodeGroup: str = "", nodeId: str = "", vars: Dict = {}
    ) -> Dict:
        """
        Environment.Control.AddContainerEnvVars Jelastic API call
        """
        return self.japic._(
            "Environment.Control.AddContainerEnvVars",
            envName=envName,
            vars=json.dumps(vars),
            nodeGroup=nodeGroup,
            nodeId=nodeId,
        )

    def AttachEnvGroup(
        self, envName: str, envGroup: str = "", envGroups: str = ""
    ) -> Dict:
        """
        Environment.Control.AttachEnvGroup Jelastic API call
        """
        return self.japic._(
            "Environment.Control.AttachEnvGroup",
            envName=envName,
            envGroup=envGroup,
            envGroups=envGroups,
        )

    def DetachEnvGroup(
        self, envName: str, envGroup: str = "", envGroups: str = ""
    ) -> Dict:
        """
        Environment.Control.DetachEnvGroup Jelastic API call
        """
        return self.japic._(
            "Environment.Control.DetachEnvGroup",
            envName=envName,
            envGroup=envGroup,
            envGroups=envGroups,
        )

    def RestartNodes(
        self,
        envName: str,
        nodeGroup: str = "",
        nodeId: str = "",
        delay: int = 0,
        isSequential: bool = None,
    ) -> Dict:
        """
        Environment.Control.RestartNodes Jelastic API call
        """
        return self.japic._(
            "Environment.Control.RestartNodes",
            envName=envName,
            nodeGroup=nodeGroup,
            nodeId=nodeId,
            delay=delay,
            isSequential=isSequential,
        )
