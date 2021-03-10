from enum import Enum
from functools import lru_cache
from json import dumps as jsondumps
from typing import Any, Dict, List, Optional

from ..exceptions import JelasticObjectException
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import _JelasticObject, _JelAttrList, _JelAttrStr
from .node import JelasticNode


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
    nodes = _JelAttrList(checked_for_differences=False)

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
        return JelasticEnvironment(
            jelastic_env=response["env"],
            env_groups=response.get("envGroups", []),
            nodes=response.get("nodes", []),
        )

    @staticmethod
    @lru_cache(maxsize=1)
    def list() -> Dict[str, "JelasticEnvironment"]:
        """
        Static method to get all environments
        """
        # This is needed as it's a static method
        from .. import api_connector as jelapi_connector

        response = jelapi_connector()._("Environment.Control.GetEnvs")
        return {
            info["env"]["envName"]: JelasticEnvironment(
                jelastic_env=info["env"],
                env_groups=info.get("envGroups", []),
                nodes=info.get("nodes", []),
            )
            for info in response["infos"]
        }

    def _update_from_getEnvInfo(
        self,
        jelastic_env: Dict[str, Any],
        env_groups: Optional[List[str]] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._env = jelastic_env
        # Read-only attributes
        self._shortdomain = self._env["shortdomain"]
        self._envName = self._env["envName"]
        self._domain = self._env["domain"]

        # Read-write attributes
        # displayName is sometimes not-present, do not die
        self.displayName = self._env.get("displayName", "")
        self.status = next(
            (status for status in self.Status if status.value == self._env["status"]),
            self.Status.UNKNOWN,
        )
        self.extdomains = self._env["extdomains"]

        self.envGroups = env_groups if env_groups else []
        self.nodes = (
            [JelasticNode(parent=self, node_from_env=node) for node in nodes]
            if nodes
            else []
        )

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __init__(
        self,
        *,
        jelastic_env: Dict[str, Any],
        env_groups: Optional[List[str]] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Construct a JelasticEnvironment from various data sources
        """
        self._update_from_getEnvInfo(jelastic_env, env_groups, nodes)

    def refresh_from_api(self) -> None:
        response = self.api._("Environment.Control.GetEnvInfo", envName=self.envName)
        self._update_from_getEnvInfo(
            jelastic_env=response["env"],
            env_groups=response.get("envGroups", []),
            nodes=response.get("nodes", []),
        )
        # api_nodes = response.get("nodes", [])
        # # Remove the nodes not anymore in the API response
        # for node in self.nodes:
        #     if not any(node.id == n.id for n in api_nodes):
        #         self.nodes.remove(node)
        #     else:
        #         # Update the present ones
        #         node._update_from_dict(
        #             envName=self.envName,
        #             node_from_env=next(n for n in api_nodes if n["id"] == node.id),
        #         )
        # # Instantiate the new ones
        # for rn in api_nodes:
        #     if rn["id"] not in [n.id for n in self.nodes]:
        #         self.nodes.append(JelasticNode(envName=self.envName, node_from_env=rn))

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
            self._from_api["envGroups"] = self.envGroups

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

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._save_displayName()
        self._save_envGroups()
        self._save_extDomains()
        self._set_running_status(self.status)
        for n in self.nodes:
            n.save()

    def node_by_node_group(self, node_group: str) -> JelasticNode:
        """
        Return a node by nodeGroup magic string
        """
        valid_node_groups = [ng.value for ng in JelasticNode.NodeGroup]
        if node_group not in valid_node_groups:
            raise JelasticObjectException(
                f"node_group value {node_group} not in {valid_node_groups}"
            )

        for node in self.nodes:
            if node.nodeGroup.value == node_group:
                return node

        raise JelasticObjectException(
            f"node_group {node_group} not find in environment's nodes"
        )

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
