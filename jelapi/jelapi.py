import json
import time
from functools import lru_cache
from typing import Any, Dict, List

from .connector import JelasticAPIConnector


class JelasticEnv:
    """
    Convenience "Env" storage class
    """

    def __init__(self, apidict: Dict) -> None:
        self.name = apidict["env"]["envName"]
        self.id = apidict["env"]["appid"]
        self.env = apidict
        self.envGroups = set(apidict["envGroups"])

    def hasEnvGroups(self, envGroups: List[str]) -> bool:
        """
        Check that this env has a set of envGroups
        """
        return set(envGroups).issubset(self.envGroups)

    def getDockerNodes(self, dockerName: str, dockerTag: str = "latest") -> List[Any]:
        """
        Get the jelastic Nodes that match the dockerName and dockerTag
        """
        return [
            node
            for node in self.env["nodes"]
            if (
                node["nodeType"] == "docker"
                and "customitem" in node
                and node["customitem"]["dockerName"] == dockerName
                and node["customitem"]["dockerTag"] == dockerTag
            )
        ]


class JelasticAPI:
    def __init__(self, apiurl: str, apitoken: str) -> None:
        """
        Get all needed data to connect to a Jelastic API
        """
        self.japic = JelasticAPIConnector(apiurl=apiurl, apitoken=apitoken)

    def test(self) -> Dict:
        """
        Test that the connection to the Jelastic API works.
        """
        return self.japic._("Users.Account.GetUserInfo")

    @property  # type: ignore
    @lru_cache(maxsize=None)
    def envs(self) -> List[JelasticEnv]:
        """
        Get the dict of environments from the API
        """
        response = self.japic._("Environment.Control.GetEnvs")
        return [JelasticEnv(env) for env in response["infos"]]

    @lru_cache(maxsize=None)
    def getEnvByName(self, name: str) -> JelasticEnv:
        """
        Get JelasticEnv object, by name
        """
        return JelasticEnv(self.japic._("Environment.Control.GetEnvInfo", envName=name))

    def getEnvsByEnvGroups(self, envGroups: List[str]) -> List[JelasticEnv]:
        """
        Get environments that match the envGroups' array
        """
        return [e for e in self.envs if e.hasEnvGroups(envGroups)]  # type: ignore

    def clear_envs(self) -> None:
        type(self).envs.fget.cache_clear()  # type: ignore
        self.getEnvByName.cache_clear()

    def cloneEnv(self, sourceEnv: JelasticEnv, destEnvName: str) -> JelasticEnv:
        """
        Clone source environment to dstEnvName.
        """
        self.japic._(
            "Environment.Control.CloneEnv",
            srcEnvName=sourceEnv.name,
            dstEnvName=destEnvName,
        )
        self.clear_envs()
        return self.getEnvByName(name=destEnvName)

    def deleteEnv(self, env: JelasticEnv, **kwargs) -> None:
        """
        Delete environment, provided that we gave it the right argument as kwarg, not just a boolean
        """
        if kwargs.get("reallySure", False):
            self.japic._("Environment.Control.DeleteEnv", envName=env.name)
            self.clear_envs()

    def attachEnvGroup(self, env: JelasticEnv, envGroup: str) -> None:
        """
        Attach an EnvGroup to a JelasticEnv
        """
        self.japic._(
            "Environment.Control.AttachEnvGroup", envName=env.name, envGroup=envGroup
        )
        self.clear_envs()

    def detachEnvGroup(self, env: JelasticEnv, envGroup: str) -> None:
        """
        Detach an EnvGroup from a JelasticEnv
        """
        self.japic._(
            "Environment.Control.DetachEnvGroup", envName=env.name, envGroup=envGroup
        )
        self.clear_envs()

    def addContainerEnvVars(
        self, env: JelasticEnv, envVars: Dict, nodeGroup: str = "cp"
    ) -> None:
        """
        Add (=overwrite) container Environment Variables in given nodeGroup
        """
        self.japic._(
            "Environment.Control.AddContainerEnvVars",
            envName=env.name,
            vars=json.dumps(envVars),
            nodeGroup=nodeGroup,
        )
        self.clear_envs()

    def getContainerEnvVarsByGroup(
        self, env: JelasticEnv, nodeGroup: str = "cp"
    ) -> None:
        """
        Get container Environment Variables in given nodeGroup
        """
        return self.japic._(
            "Environment.Control.GetContainerEnvVarsByGroup",
            envName=env.name,
            nodeGroup="cp",
        )

    def redeployContainersByGroup(
        self, env: JelasticEnv, dockertag: str, nodeGroup: str = "cp"
    ) -> None:
        """
        Trigger redeployment of the containers of the given env, to the given dockertag, from the given nodeGroup
        """
        self.japic._(
            "Environment.Control.RedeployContainersByGroup",
            tag=dockertag,
            nodeGroup=nodeGroup,
            envName=env.name,
        )

    def removeAllExtIPs(self, env: JelasticEnv, nodeGroup: str = "bl") -> None:
        """
        Remove all external IPs from given environment to reduce cost (and break custom SSL)
        """
        for ipType in ["ipv4", "ipv6"]:
            self.japic._(
                "Environment.Binder.SetExtIpCount",
                appid=env.id,
                nodeGroup=nodeGroup,
                type=ipType,
                count=0,
            )

    def swapExtIP(
        self, env: JelasticEnv, source_node_id: str, target_node_id: str, ip: str
    ) -> None:
        """
        Swap an external ip from a node to another one
        """
        self.japic._(
            "Environment.Binder.SwapExtIps",
            envName=env.name,
            sourceNodeId=source_node_id,
            targetNodeId=target_node_id,
            sourceIp=ip,
            targetIp=ip,
        )

    def setBuiltInSSL(self, env: JelasticEnv, sslstate: bool) -> None:
        """
        Set built-in SSL at environment level.
        """
        self.japic._(
            "Environment.Control.EditEnvSettings",
            envName=env.name,
            settings=json.dumps({"sslstate": sslstate}),
        )

    def execCmdByGroup(self, env: JelasticEnv, nodeGroup: str, command: str) -> None:
        """
        Launch a specific command in a node group
        """
        self.japic._(
            "Environment.Control.ExecCmdByGroup",
            envName=env.name,
            nodeGroup=nodeGroup,
            commandList=json.dumps([{"command": command, "params": ""}]),
        )

    def setEnvDisplayName(self, env: JelasticEnv, displayName: str) -> None:
        """
        Set the environment Display Name
        """
        self.japic._(
            "Environment.Control.SetEnvDisplayName",
            envName=env.name,
            displayName=displayName,
        )

    def sleepEnv(self, env: JelasticEnv) -> None:
        """
        Gets running environment asleep
        """
        self.japic._("Environment.Control.SleepEnv", envName=env.name)

    def startEnv(self, env: JelasticEnv) -> None:
        """
        Starts environment if it is stopped
        """
        self.japic._("Environment.Control.StartEnv", envName=env.name)

    def stopEnv(self, env: JelasticEnv) -> None:
        """
        Stops an environment if it is running
        """
        self.japic._("Environment.Control.StopEnv", envName=env.name)

    def getExtendedAccountBillingHistoryByPeriod(
        self, env: JelasticEnv, start_time: str, end_time: str
    ) -> Dict:
        """
        Get the billing details for an environment
        start_time and end_time can have the following formats: 2021-01-19, 2021-01-19T00:00:00
        """
        # adapt the time to reflect the timezone of the location of the script
        time_offset = int(time.timezone * -1 / 60)
        return self.japic._(
            "Billing.Account.GetExtendedAccountBillingHistoryByPeriod",
            appId=env.id,
            starttime=start_time,
            endtime=end_time,
            targetAppid=env.id,
            timeOffset=time_offset,
        )
