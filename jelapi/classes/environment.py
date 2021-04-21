from copy import deepcopy
from enum import Enum
from functools import lru_cache
from json import dumps as jsondumps
from typing import Any, Dict, List, Optional

from ..exceptions import JelasticObjectException, deprecation
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import (
    _JelasticObject,
    _JelAttrBool,
    _JelAttrDict,
    _JelAttrList,
    _JelAttrStr,
)
from .node import JelasticNode
from .nodegroup import JelasticNodeGroup


class JelasticEnvironment(_JelasticObject):
    """
    Represents a Jelastic Environment
    """

    class Status(Enum):
        """
        Standard statuses
        Latest reference https://github.com/jelastic/localizations/blob/master/English/5.4/%5Blang-en.js%5D#L999
        """

        UNKNOWN = 0
        RUNNING = 1
        STOPPED = 2
        LAUNCHING = 3
        SLEEPING = 4
        SUSPENDED = 5
        CREATING = 6
        CLONING = 7
        UPDATING = 12

    displayName = _JelAttrStr()
    envGroups = _JelAttrList()
    status = _JelAttr()
    envName = _JelAttrStr(read_only=True)
    shortdomain = _JelAttrStr(read_only=True)
    domain = _JelAttrStr(read_only=True)
    extdomains = _JelAttrList()
    nodeGroups = _JelAttrDict(checked_for_differences=False)
    ishaneabled = _JelAttrBool(read_only=True)
    hardwareNodeGroup = _JelAttrStr(read_only=True)
    sslstate = _JelAttrBool()

    @staticmethod
    def get(envName: str) -> "JelasticEnvironment":
        """
        Static method to get one environment
        """
        # This is needed as it's a static method
        from .. import api_connector as jelapi_connector

        response = jelapi_connector()._(
            "Environment.Control.GetEnvInfo", envName=envName
        )
        j = JelasticEnvironment()
        j.update_from_env_dict(response["env"])
        j.update_env_groups_from_info(response.get("envGroups", []))
        j.update_node_groups_from_info(response.get("nodeGroups", []))
        j.update_nodes_from_info(response.get("nodes", []))
        return j

    @staticmethod
    @lru_cache(maxsize=1)
    def list() -> Dict[str, "JelasticEnvironment"]:
        """
        Static method to get all environments
        """
        # This is needed as it's a static method
        from .. import api_connector as jelapi_connector

        response = jelapi_connector()._("Environment.Control.GetEnvs")
        envs = {}
        for info in response["infos"]:
            name = info["env"]["envName"]
            envs[name] = JelasticEnvironment()
            envs[name].update_from_env_dict(info["env"])
            envs[name].update_env_groups_from_info(info.get("envGroups", []))
            envs[name].update_node_groups_from_info(info.get("nodeGroups", []))
            envs[name].update_nodes_from_info(info.get("nodes", []))

        return envs

    def clone(self, cloned_environment_name: str) -> "JelasticEnvironment":
        """
        Clone an environment, and return a new JelasticEnvironment matching the new one
        """
        if len(cloned_environment_name) > 33:
            raise JelasticObjectException(
                "New environments' names cannot be longer than 33 characters"
            )
        self.api._(
            "Environment.Control.CloneEnv",
            srcEnvName=self.envName,
            dstEnvName=cloned_environment_name,
        )
        return JelasticEnvironment.get(envName=cloned_environment_name)

    def attach_node_group(self, node_group: JelasticNodeGroup) -> None:
        """
        Make sure a node_group is attached correctly to that Environment
        """
        self.nodeGroups[node_group.nodeGroupType.value] = node_group
        node_group._parent = self

    def update_from_env_dict(self, jelastic_env_dict: Dict[str, Any]) -> None:
        """
        Update from the environment dict as gotten from API
        """
        # Allow exploration of the returned object, but don't act on it.
        self._env = jelastic_env_dict
        # Read-only attributes
        self._shortdomain = self._env["shortdomain"]
        self._envName = self._env["envName"]
        self._domain = self._env["domain"]
        self._hardwareNodeGroup = self._env["hardwareNodeGroup"]
        self._sslstate = self._env["sslstate"]
        self._ishaneabled = self._env["ishaenabled"]

        # Read-write attributes
        # displayName is sometimes not-present, do not die
        self.displayName = self._env.get("displayName", "")
        self.status = next(
            (status for status in self.Status if status.value == self._env["status"]),
            self.Status.UNKNOWN,
        )
        self.extdomains = self._env["extdomains"]

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def update_env_groups_from_info(self, env_groups: List[str]) -> None:
        """
        Update the envGroups as coming from API
        """
        self.envGroups = env_groups
        self.copy_self_as_from_api("envGroups")

    def update_node_groups_from_info(self, node_groups: List[Dict[str, Any]]) -> None:
        """
        Set the node groups (as gotten from API)
        """
        if not hasattr(self, "_envName"):
            raise JelasticObjectException(
                "update_node_groups: envName unset; call update_from_env_dict() first !"
            )

        for node_group_from_env in node_groups:
            node_group = JelasticNodeGroup()
            node_group.update_from_env_dict(node_group_from_env=node_group_from_env)
            node_group.attach_to_environment(self)

        self.copy_self_as_from_api("nodeGroups")

    def update_nodes_from_info(self, nodes: List[Dict[str, Any]]) -> None:
        """
        Construct/Update the nodes
        """
        if not hasattr(self, "_envName"):
            raise JelasticObjectException(
                "update_nodes: envName unset; call update_from_env_dict() first !"
            )

        for ng in self.nodeGroups.values():
            ng.nodes = []

        # Now add nodes in the nodeGroup
        for node_dict in nodes:
            if node_dict["nodeGroup"] not in self.nodeGroups:
                raise JelasticObjectException(
                    "Environment got a node outside of one of its nodeGroups"
                )

            node_group = self.nodeGroups[node_dict["nodeGroup"]]
            jelnode = JelasticNode()
            jelnode.update_from_env_dict(node_from_env=node_dict)
            jelnode.attach_to_node_group(node_group)

            node_group.copy_self_as_from_api("nodes")

    def __init__(
        self,
        *,
        jelastic_env: Dict[str, Any] = None,
        env_groups: Optional[List[str]] = None,
        node_groups: Optional[List[Dict[str, Any]]] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Construct a JelasticEnvironment from various data sources
        """
        super().__init__()
        if not hasattr(self, "nodeGroup"):
            self.nodeGroups = {}
        if not hasattr(self, "envGroups"):
            self.envGroups = []

        if jelastic_env:
            deprecation(
                "JelasticEnvironment.__init__(): passing jelastic_env is deprecated; use update_from_env_dict() instead"
            )
            self.update_from_env_dict(jelastic_env)

        if env_groups:
            deprecation(
                "JelasticEnvironment.__init__(): passing env_groups is deprecated; use update_env_groups_from_info() instead"
            )

            self.update_env_groups_from_info(env_groups)

        if node_groups:
            deprecation(
                "JelasticEnvironment.__init__(): passing node_groups is deprecated; use update_node_groups_from_info() instead"
            )
            self.update_node_groups_from_info(node_groups)

        if nodes:
            deprecation(
                "JelasticEnvironment.__init__(): passing nodes is deprecated; use update_nodes_from_info() instead"
            )
            self.update_nodes_from_info(nodes)

    def refresh_from_api(self) -> None:
        response = self.api._("Environment.Control.GetEnvInfo", envName=self.envName)
        self.update_from_env_dict(response["env"])

        self.update_env_groups_from_info(response.get("envGroups", []))
        self.update_node_groups_from_info(response.get("nodeGroups", []))
        self.update_nodes_from_info(response.get("nodes", []))

    def __str__(self) -> str:
        return f"JelasticEnvironment '{self.envName}' <https://{self.domain}>"

    def _save_displayName(self):
        """
        Propagate the displayName change to the Jelastic API
        """
        if self.displayName != self._from_api["displayName"]:
            self.api._(
                "Environment.Control.SetEnvDisplayName",
                envName=self.envName,
                displayName=self.displayName,
            )
            self._from_api["displayName"] = self.displayName

    def _save_envGroups(self):
        """
        Propagate the envGroups change to the Jelastic API
        """
        if self.envGroups != self._from_api["envGroups"]:
            self.api._(
                "Environment.Control.SetEnvGroup",
                envName=self.envName,
                envGroups=jsondumps(self.envGroups),
            )
            self.copy_self_as_from_api("envGroups")

    def _save_extDomains(self):
        """
        Ensure the extDomains are bound correctly
        """
        if self.extdomains != self._from_api["extdomains"]:
            # Remove domains
            for domain in self._from_api["extdomains"]:
                if domain not in self.extdomains:
                    self.api._(
                        "Environment.Binder.RemoveExtDomain",
                        envName=self.envName,
                        extdomain=domain,
                    )
            # Add domains
            for domain in self.extdomains:
                if domain not in self._from_api["extdomains"]:
                    self.api._(
                        "Environment.Binder.BindExtDomain",
                        envName=self.envName,
                        extdomain=domain,
                    )
            self._from_api["extdomains"] = self.extdomains

    def _set_running_status(self, to_status_now: Status):
        """
        Put Environment in the right status
        """
        self.status = to_status_now

        if self.status != self._from_api["status"]:
            if self.status == self.Status.RUNNING:
                # TODO limit the statuses from which this is possible
                self.api._(
                    "Environment.Control.StartEnv",
                    envName=self.envName,
                )
                self._from_api["status"] = self.Status.RUNNING
            elif self.status == self.Status.STOPPED:
                if self._from_api["status"] not in [self.Status.RUNNING]:
                    raise JelasticObjectException(
                        "Cannot stop an environment not running"
                    )
                self.api._(
                    "Environment.Control.StopEnv",
                    envName=self.envName,
                )
                self._from_api["status"] = self.Status.STOPPED
            elif self.status == self.Status.SLEEPING:
                self.api._(
                    "Environment.Control.SleepEnv",
                    envName=self.envName,
                )
                self._from_api["status"] = self.Status.SLEEPING
            else:
                raise JelasticObjectException(
                    f"{self.__class__.__name__}: {self.status} not supported"
                )

    def get_topology(self) -> Dict[str, Any]:
        """
        Return the "Environment" topology, as consumed by ChangeTopology
        See https://docs.jelastic.com/api/5.9.8/public/#!/api/environment.Control-method-ChangeTopology
        """
        return {
            "displayName": self.displayName,
            "ishaenabled": self.ishaneabled,
            "region": self.hardwareNodeGroup,
            "shortdomain": self.shortdomain,
            "sslstate": self.sslstate,
        }
        # Missing keys:
        # "engine": "string",

    def _save_topology_and_node_groups(self):
        """
        Save the topology (nodeGroups, sslstate and others), then the nodeGroups'.
        """
        # Determine if a topology change is needed
        if (
            "nodeGroups" not in self._from_api
            or len(self._from_api["nodeGroups"]) != len(self.nodeGroups)
            or any(ng.needs_topology_update() for ng in self.nodeGroups.values())
            or self.sslstate != self._from_api["sslstate"]
        ):
            # We need to force the API to match what we want.
            # First, no wipeout of nodeGroups
            if len(self.nodeGroups) == 0:
                raise JelasticObjectException("Wipeout of nodeGroups not allowed")

            # Backup the stuff we want to keep after topology change
            wanted_node_groups = deepcopy(self.nodeGroups)

            apiresponse = self.api._(
                "Environment.Control.ChangeTopology",
                envName=self.envName,
                env=jsondumps(self.get_topology()),
                nodes=jsondumps([ng.get_topology() for ng in self.nodeGroups.values()]),
            )
            response = apiresponse["response"]

            self.update_from_env_dict(response["env"])
            self.update_env_groups_from_info(response.get("envGroups", []))
            self.nodeGroups = wanted_node_groups
            self.update_nodes_from_info(response.get("nodes", []))

            for k, ng in self.nodeGroups.items():
                for n in ng.nodes:
                    n.copy_self_as_from_api()

                # Complex ones
                ng.copy_self_as_from_api("_envVars")
                ng.copy_self_as_from_api("_links")
                ng.copy_self_as_from_api("_containerVolumes")

                # Bare attributes
                ng.copy_self_as_from_api("displayName")
                ng.copy_self_as_from_api("isSLBAccessEnabled")

                # Make sure these get saved afterwards
                ng._from_api["_mountPoints"] = []

        for ng in self.nodeGroups.values():
            ng.save()
        self._from_api["nodeGroups"] = self.nodeGroups

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._save_displayName()
        self._save_envGroups()
        self._save_extDomains()
        self._set_running_status(self.status)
        self._save_topology_and_node_groups()

    def node_by_node_group(self, node_group: str) -> JelasticNode:
        """
        Return a node by nodeGroup magic string
        """
        valid_node_groups = [ng.value for ng in JelasticNodeGroup.NodeGroupType]
        if node_group not in valid_node_groups:
            raise JelasticObjectException(
                f"node_group value {node_group} not in {valid_node_groups}"
            )

        try:
            return self.nodeGroups[node_group].nodes[0]
        except (IndexError, KeyError):
            raise JelasticObjectException(
                f"node_group {node_group} not found in environment's nodes"
            )

    def get_sumstats(self, duration_in_seconds: int) -> List[str]:
        """
        Get usage stats
        """
        response = self.api._(
            "Environment.Control.GetSumStat",
            envName=self.envName,
            duration=duration_in_seconds,
        )
        return response["stats"]

    def start(self) -> None:
        """
        Start Environment immediately
        """
        self._set_running_status(self.Status.RUNNING)

    def stop(self) -> None:
        """
        Stop Environment immediately
        """
        self._set_running_status(self.Status.STOPPED)

    def sleep(self) -> None:
        """
        Put Environment to sleep immediately
        """
        self._set_running_status(self.Status.SLEEPING)
