import json
from enum import Enum
from typing import Any, Dict

from ..exceptions import JelasticObjectException
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import (
    _JelasticObject,
    _JelAttrDict,
    _JelAttrInt,
    _JelAttrIPv4,
    _JelAttrStr,
)


class JelasticNode(_JelasticObject):
    """
    Represents a Jelastic Node
    """

    class NodeGroup(Enum):
        """
        Standard NodeGroups
        """

        LOAD_BALANCER = "bl"
        APPLICATION_SERVER = "cp"
        CACHE = "cache"
        SQL_DATABASE = "sqldb"
        NOSQL_DATABASE = "nosqldb"
        STORAGE_CONTAINER = "storage"

    id = _JelAttrInt(read_only=True)
    envName = _JelAttrStr(read_only=True)
    intIP = _JelAttrIPv4(read_only=True)
    url = _JelAttrStr(read_only=True)
    nodeGroup = _JelAttr(read_only=True)
    # "always guaranteed minimum"
    fixedCloudlets = _JelAttrInt()
    # "maximum"
    flexibleCloudlets = _JelAttrInt()
    # Variables
    _envVars = (
        _JelAttrDict()
    )  # this is the JelAttr, use envVars to access them through lazy loading

    def _update_from_dict(self, envName: str, node_from_env: Dict[str, Any]) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._node = node_from_env
        # Read-only attributes
        self._envName = envName
        for attr in ["id", "intIP", "url"]:
            setattr(self, f"_{attr}", self._node[attr])

        self._nodeGroup = next(
            (ng for ng in self.NodeGroup if ng.value == self._node["nodeGroup"]),
        )

        # RW attrs
        for attr in ["fixedCloudlets", "flexibleCloudlets"]:
            setattr(self, attr, self._node[attr])

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __init__(self, *, envName: str, node_from_env: Dict[str, Any]) -> None:
        """
        Construct a JelasticNode from the outer data
        """
        self._update_from_dict(envName=envName, node_from_env=node_from_env)

    def refresh_from_api(self) -> None:
        """
        JelasticNodes cannot be refreshed by themselves; refresh the parent JelasticEnvironment
        """
        pass

    def __str__(self) -> str:
        return f"JelasticNode id:{self.id}"

    def _set_cloudlets(self):
        if (
            self._from_api["fixedCloudlets"] != self.fixedCloudlets
            or self._from_api["flexibleCloudlets"] != self.flexibleCloudlets
        ):
            # TODO: Add a boolean to explicitely allow reducing the number of flexibleCloudlets
            self.api._(
                "Environment.Control.SetCloudletsCountById",
                envName=self.envName,
                count=1,  # TODO: this is the nunber of _nodes
                nodeid=self.id,
                fixedCloudlets=self.fixedCloudlets,
                flexibleCloudlets=self.flexibleCloudlets,
            )
            self._from_api["fixedCloudlets"] = self.fixedCloudlets
            self._from_api["flexibleCloudlets"] = self.flexibleCloudlets

    @property
    def envVars(self):
        """
        Lazy load envVars when they're accessed
        """
        if not hasattr(self, "_envVars"):
            response = self.api._(
                "Environment.Control.GetContainerEnvVars",
                envName=self.envName,
                nodeId=self.id,
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
            if self._from_api["_envVars"] != self._envVars:
                self.api._(
                    "Environment.Control.SetContainerEnvVars",
                    envName=self.envName,
                    nodeId=self.id,
                    vars=json.dumps(self._envVars),
                )
                self.copy_self_as_from_api("_envVars")

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._set_cloudlets()
        self._set_env_vars()
