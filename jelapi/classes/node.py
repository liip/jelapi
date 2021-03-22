import json
from enum import Enum
from typing import Any, Dict, List

from ..exceptions import JelasticObjectException
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import (
    _JelasticObject,
    _JelAttrBool,
    _JelAttrDict,
    _JelAttrInt,
    _JelAttrIPv4,
    _JelAttrList,
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

    # TODO: make the ones that make sense as RW attributes
    diskIoLimit = _JelAttrInt(read_only=True)
    diskIopsLimit = _JelAttrInt(read_only=True)
    diskLimit = _JelAttrInt(read_only=True)
    endpoints = _JelAttrList(read_only=True)
    features = _JelAttrList(read_only=True)
    hasPackages = _JelAttrBool(read_only=True)
    isClusterSupport = _JelAttrBool(read_only=True)
    isCustomSslSupport = _JelAttrBool(read_only=True)
    isExternalIpRequired = _JelAttrBool(read_only=True)
    isHighAvailability = _JelAttrBool(read_only=True)
    isResetPassword = _JelAttrBool(read_only=True)
    isVcsSupport = _JelAttrBool(read_only=True)
    isWebAccess = _JelAttrBool(read_only=True)
    ismaster = _JelAttrBool(read_only=True)
    maxchanks = _JelAttrInt(read_only=True)
    messages = _JelAttrList(read_only=True)
    name = _JelAttrStr(read_only=True)
    nodeType = _JelAttrStr(read_only=True)
    nodemission = _JelAttrStr(read_only=True)
    osType = _JelAttrStr(read_only=True)
    packages = _JelAttrList(read_only=True)
    port = _JelAttrInt(read_only=True)
    singleContext = _JelAttrBool(read_only=True)
    status = _JelAttrInt(read_only=True)
    type = _JelAttrStr(read_only=True)
    version = _JelAttrStr(read_only=True)

    # "always guaranteed minimum"
    fixedCloudlets = _JelAttrInt()
    # "maximum"
    flexibleCloudlets = _JelAttrInt()
    # Variables
    _envVars = (
        _JelAttrDict()
    )  # this is the JelAttr, use envVars to access them through lazy loading

    def _update_from_dict(self, parent, node_from_env: Dict[str, Any]) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._node = node_from_env
        self._parent = parent
        # Read-only attributes
        self._envName = self._parent.envName
        for attr in [
            "id",
            "intIP",
            "url",
            "diskIoLimit",
            "diskIopsLimit",
            "diskLimit",
            "endpoints",
            "features",
            "hasPackages",
            "isClusterSupport",
            "isCustomSslSupport",
            "isExternalIpRequired",
            "isHighAvailability",
            "isResetPassword",
            "isVcsSupport",
            "isWebAccess",
            "ismaster",
            "maxchanks",
            "messages",
            "name",
            "nodeType",
            "nodemission",
            "osType",
            "packages",
            "port",
            "singleContext",
            "status",
            "type",
            "url",
            "version",
        ]:
            setattr(self, f"_{attr}", self._node[attr])

        self._nodeGroup = next(
            (ng for ng in self.NodeGroup if ng.value == self._node["nodeGroup"]),
        )

        # RW attrs
        for attr in ["fixedCloudlets", "flexibleCloudlets"]:
            setattr(self, attr, self._node[attr])

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __init__(self, *, parent, node_from_env: Dict[str, Any]) -> None:
        """
        Construct a JelasticNode from the outer data
        """
        self._update_from_dict(parent=parent, node_from_env=node_from_env)

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
            if len(self._envVars) == 0:
                raise JelasticObjectException(
                    "envVars cannot be set to empty (no wipe out)"
                )
            if self._from_api["_envVars"] != self._envVars:
                # Only remove vars that need to be removed
                vars_to_remove = [
                    k
                    for k, v in self._from_api["_envVars"].items()
                    if k not in self._envVars
                ]

                # Only add or update vars that need doing so.
                vars_to_add_or_update = {
                    k: v
                    for k, v in self._envVars.items()
                    if k not in self._from_api["_envVars"]
                    or v != self._from_api["_envVars"][k]
                }
                if len(vars_to_remove) > 0:
                    if len(vars_to_add_or_update) > 0:
                        # Both need doing, do one shot only
                        self.api._(
                            "Environment.Control.SetContainerEnvVars",
                            envName=self.envName,
                            nodeId=self.id,
                            vars=json.dumps(self._envVars),
                        )
                    else:
                        self.api._(
                            "Environment.Control.RemoveContainerEnvVars",
                            envName=self.envName,
                            nodeId=self.id,
                            vars=json.dumps(vars_to_remove),
                        )
                elif len(vars_to_add_or_update) > 0:
                    # Add = "Set or Replace"
                    self.api._(
                        "Environment.Control.AddContainerEnvVars",
                        envName=self.envName,
                        nodeId=self.id,
                        vars=json.dumps(vars_to_add_or_update),
                    )

                self.copy_self_as_from_api("_envVars")

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._set_cloudlets()
        self._set_env_vars()

    def execute_commands(self, commands: List[str]) -> List[Dict[str, str]]:
        """
        Execute a list of commands in this node
        """
        if not isinstance(commands, list):
            raise TypeError("execute_commands() takes a a list of commands")
        command_list = [{"command": cmd, "params": ""} for cmd in commands]
        command_results = self.api._(
            "Environment.Control.ExecCmdById",
            envName=self.envName,
            nodeid=self.id,
            commandList=json.dumps(command_list),
        )
        return [
            {k: cr[k] for k in ["out", "result", "errOut"]}
            for cr in command_results["responses"]
        ]

    def execute_command(self, command: str) -> Dict[str, str]:
        """
        Execute a single command in this node
        """
        if not isinstance(command, str):
            raise TypeError("execute_command() takes a string as command")
        return self.execute_commands([command])[0]
