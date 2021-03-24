import json
from enum import Enum
from typing import Any, Dict

from ..exceptions import JelasticObjectException
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import (
    _JelasticObject,
    _JelAttrBool,
    _JelAttrDict,
    _JelAttrList,
    _JelAttrStr,
)


class JelasticNodeGroup(_JelasticObject):
    """
    Represents a Jelastic NodeGroup, a sort of collection of Nodes within an environment
    """

    class NodeGroupType(Enum):
        """
        Standard NodeGroups
        """

        LOAD_BALANCER = "bl"
        APPLICATION_SERVER = "cp"
        CACHE = "cache"
        SQL_DATABASE = "sqldb"
        NOSQL_DATABASE = "nosqldb"
        STORAGE_CONTAINER = "storage"

    nodeGroup = _JelAttr(read_only=True)
    envName = _JelAttrStr(read_only=True)

    isSLBAccessEnabled = _JelAttrBool()
    displayName = _JelAttrStr()
    nodes = _JelAttrList(checked_for_differences=False)

    # Variables
    _envVars = (
        _JelAttrDict()
    )  # this is the JelAttr, use envVars to access them through lazy loading

    @property
    def envVars(self):
        """
        Lazy load envVars when they're accessed
        """
        from .environment import JelasticEnvironment

        JelStatus = JelasticEnvironment.Status

        if self._parent.status not in [
            JelStatus.RUNNING,
            JelStatus.CREATING,
            JelStatus.CLONING,
        ]:
            raise JelasticObjectException(
                "envVars cannot be gathered on environments not running"
            )
        if not hasattr(self, "_envVars"):
            response = self.api._(
                "Environment.Control.GetContainerEnvVarsByGroup",
                envName=self.envName,
                nodeGroup=self.nodeGroup.value,
            )
            self._envVars = response["object"]
            self.copy_self_as_from_api("_envVars")
        return self._envVars

    def _set_env_vars(self):
        """
        Set the modified envVars
        """
        # Only set them if they were fetched first
        if hasattr(self, "_envVars"):
            if "_envVars" not in self._from_api:
                raise JelasticObjectException(
                    "envVars cannot be saved if not fetched first (no blind set)"
                )
            if len(self._envVars) == 0:
                raise JelasticObjectException(
                    "envVars cannot be set to empty (no wipe out)"
                )
            if self._from_api["_envVars"] != self._envVars:
                self.api._(
                    "Environment.Control.SetContainerEnvVarsByGroup",
                    envName=self.envName,
                    nodeGroup=self.nodeGroup.value,
                    data=json.dumps(self._envVars),
                )
                self.copy_self_as_from_api("_envVars")

    def _update_from_dict(self, parent, node_group_from_env: Dict[str, Any]) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._node_group = node_group_from_env
        self._parent = parent
        # Read-only attributes
        self._envName = self._parent.envName

        self._nodeGroup = next(
            (ng for ng in self.NodeGroupType if ng.value == self._node_group["name"]),
        )

        # R/W attributes
        self._displayName = self._node_group.get(
            "displayName", ""
        )  # Apparently optional
        self._isSLBAccessEnabled = self._node_group.get("isSLBAccessEnabled")

        # Start without nodes, they're added after init
        if not getattr(self, "nodes", False):
            self.nodes = []

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __init__(self, *, parent, node_group_from_env: Dict[str, Any]) -> None:
        """
        Construct a JelasticNodeGroup from the outer data
        """
        self._update_from_dict(parent=parent, node_group_from_env=node_group_from_env)

    def refresh_from_api(self) -> None:
        """
        JelasticNodeGroups should be refreshed by themselves
        """
        # TODO

    def _apply_data(self):
        """
        Use "ApplyData" to save all the data we _can_ save
        """
        #  Prepare data attr for ApplyData call
        data = {}
        for attr in ["displayName", "isSLBAccessEnabled"]:
            if self._from_api[attr] != getattr(self, attr):
                data[attr] = getattr(self, attr)
        if len(data) > 0:
            # Jelastic API 5.9
            self.api._(
                "Environment.Control.ApplyNodeGroupData",
                envName=self.envName,
                nodeGroup=self.nodeGroup.value,
                data=json.dumps(data),
            )
            for k in data.keys():
                self._from_api[k] = data[k]

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._apply_data()
        self._set_env_vars()
        for n in self.nodes:
            n.save()

    def __str__(self):
        """
        String representation
        """
        return f"JelasticNodeGroup {self.nodeGroup.value}"

    # Jelastic-related utilites
    def read_file(self, path: str) -> str:
        """
        Read a file in a nodeGroup
        """
        if not path:
            raise TypeError(f"path {path} cannot be empty")
        response = self.api._(
            "Environment.File.Read",
            envName=self.envName,
            nodeGroup=self.nodeGroup.value,
            path=path,
        )
        return response["body"]

    def redeploy(self, docker_tag: str = "latest"):
        """
        Redeploy a nodeGroup to a certain docker tag
        """
        self.api._(
            "Environment.Control.RedeployContainersByGroup",
            envName=self.envName,
            nodeGroup=self.nodeGroup.value,
            tag=docker_tag,
        )
