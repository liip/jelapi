import json
from enum import Enum
from typing import Any, Dict, List

from ..exceptions import JelasticObjectException, deprecation
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import (
    _JelasticObject,
    _JelAttrBool,
    _JelAttrInt,
    _JelAttrIPv4,
    _JelAttrList,
    _JelAttrStr,
)
from .nodegroup import JelasticNodeGroup


class JelasticNode(_JelasticObject):
    """
    Represents a Jelastic Node
    """

    class NodeType(Enum):
        """
        Available Node Types
        See https://docs.cloudscripting.com/creating-manifest/selecting-containers/#supported-stacks
        """

        DOCKER = "docker"
        STORAGE = "storage"

    id = _JelAttrInt(read_only=True)
    envName = _JelAttrStr(read_only=True)
    intIP = _JelAttrIPv4(read_only=True)
    url = _JelAttrStr(read_only=True)
    nodeGroup = _JelAttr(read_only=True)

    # Not a real attribute, at least not synced to API
    docker_registry: Dict
    docker_image = _JelAttrStr()

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
    nodeType = _JelAttr(read_only=True)
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
    allowFlexibleCloudletsReduction = _JelAttrBool(checked_for_differences=False)

    def attach_to_node_group(self, node_group: "JelasticNodeGroup") -> None:
        """
        Set the nodeGroup, with all accompanying things
        """
        node_group.append_node(self)

        # Read-only attributes
        try:
            self._envName = self._nodeGroup._parent.envName
        except AttributeError:
            # Do not set it, it'll fail the self.raise_unless_can_update_to_api() check if unset
            pass

    def update_from_env_dict(
        self,
        node_from_env: Dict[str, Any],
    ) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._node = node_from_env

        self._nodeType = next(
            (nt for nt in self.NodeType if nt.value == self._node["nodeType"]), None
        )
        if not self.nodeType:
            raise JelasticObjectException(f"nodeType unknown: {self._node['nodeType']}")

        # Mandatory attributes, raises KeyError if missing
        for attr in [
            "id",
            "name",
            "nodemission",
            "status",
            "type",
        ]:
            setattr(self, f"_{attr}", self._node[attr])

        # Ususal attributes, does not raise if inexistant
        for attr in [
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
            "osType",
            "packages",
            "port",
            "singleContext",
            "url",
            "version",
        ]:
            if attr in self._node:
                setattr(self, f"_{attr}", self._node[attr])

        # RW attrs
        for attr in ["fixedCloudlets", "flexibleCloudlets"]:
            setattr(self, attr, self._node[attr])

        if self.nodeType == self.NodeType.DOCKER:
            try:
                self.docker_image = self._node["customitem"]["dockerName"]
            except KeyError:
                self.docker_image = ""

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __init__(
        self,
        *,
        nodeType: NodeType = None,
        fixedCloudlets: int = 1,
        flexibleCloudlets: int = 2,
        node_group: "JelasticNodeGroup" = None,
        node_from_env: Dict[str, Any] = None,
    ) -> None:
        """
        Construct a JelasticNode from the outer data, or from
        """
        super().__init__()
        # By default, do not allow flexibleCloudlets' reduction
        self.allowFlexibleCloudletsReduction = False
        # Set initials
        self.fixedCloudlets = fixedCloudlets
        self.flexibleCloudlets = flexibleCloudlets

        if nodeType:
            self._nodeType = nodeType
            self._nodemission = nodeType.value

        if node_group:
            deprecation(
                "Node.__init__(): Passing node_group is deprecated; use attach_to_node_group instead",
            )
            self.attach_to_node_group(node_group)
            assert self.nodeGroup == node_group

        if node_from_env:
            deprecation(
                "Node.__init__(): Passing node_from_env is deprecated; use update_from_env_dict instead",
            )
            self.update_from_env_dict(node_from_env=node_from_env)
            assert self.is_from_api

    @property
    def links(self) -> List[Dict[str, Any]]:
        """
        Expose the inwards docker links, as they came from the API, for consumption from nodeGroup
        """
        try:
            return [
                n for n in self._node["customitem"]["dockerLinks"] if n["type"] == "IN"
            ]
        except (KeyError, AttributeError):
            return []

    def __str__(self) -> str:
        return f"JelasticNode id:{self.id}"

    def _set_cloudlets(self):
        """
        Set the cloudlets' count on that node
        """
        self.raise_unless_can_update_to_api()

        if not self._from_api or (
            self._from_api["fixedCloudlets"] != self.fixedCloudlets
            or self._from_api["flexibleCloudlets"] != self.flexibleCloudlets
        ):
            if self.flexibleCloudlets < self._from_api["flexibleCloudlets"]:
                if not self.allowFlexibleCloudletsReduction:
                    raise JelasticObjectException(
                        "flexibleCloudlets cannot be reduced without setting allowFlexibleCloudletsReduction to True before save()"
                    )
                else:
                    # Reset the authorization to False
                    self.allowFlexibleCloudletsReduction = False
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
        Access the lazy-loaded vars from the nodeGroup, always
        """
        try:
            return self._nodeGroup.envVars
        except AttributeError:
            raise JelasticObjectException(
                "Cannot fetch envVars from node without nodeGroup (not from API ?)"
            )

    def raise_unless_can_update_to_api(self):
        """
        Check if we can update to API, or raise
        """
        if not hasattr(self, "envName"):
            raise JelasticObjectException(
                "Cannot update to API, use attach_to_node_group() before saving!"
            )

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._set_cloudlets()

    # Jelastic-related utilities
    def execute_commands(self, commands: List[str]) -> List[Dict[str, str]]:
        """
        Execute a list of commands in this node
        """
        if not isinstance(commands, list):
            raise TypeError("execute_commands() takes a a list of commands")

        self.raise_unless_can_update_to_api()

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

    def read_file(self, path: str) -> str:
        """
        Read a file in a node
        """
        if not path:
            raise TypeError(f"path {path} cannot be empty")

        self.raise_unless_can_update_to_api()

        response = self.api._(
            "Environment.File.Read",
            envName=self.envName,
            nodeid=self.id,
            path=path,
        )
        return response["body"]
