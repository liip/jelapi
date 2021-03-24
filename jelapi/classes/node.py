import json
from typing import Any, Dict, List

from ..exceptions import JelasticObjectException
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
    allowFlexibleCloudletsReduction = _JelAttrBool(checked_for_differences=False)

    def _update_from_dict(
        self,
        node_group: "JelasticNodeGroup",
        node_from_env: Dict[str, Any],
    ) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._node = node_from_env
        self._nodeGroup = node_group

        # Read-only attributes
        self._envName = self._nodeGroup._parent.envName

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

        # RW attrs
        for attr in ["fixedCloudlets", "flexibleCloudlets"]:
            setattr(self, attr, self._node[attr])
        # By default, do not allow flexibleCloudlets' reduction
        self.allowFlexibleCloudletsReduction = False

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __init__(
        self,
        *,
        node_group: "JelasticNodeGroup",
        node_from_env: Dict[str, Any],
    ) -> None:
        """
        Construct a JelasticNode from the outer data
        """
        self._update_from_dict(node_group=node_group, node_from_env=node_from_env)

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
        return self._nodeGroup.envVars

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
        response = self.api._(
            "Environment.File.Read",
            envName=self.envName,
            nodeid=self.id,
            path=path,
        )
        return response["body"]
