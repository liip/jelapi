from typing import Any, Dict

from .jelasticobject import (
    _JelasticObject,
    _JelAttrStr,
    _JelAttrInt,
    _JelAttrIPv4,
)


class JelasticNode(_JelasticObject):
    """
    Represents a Jelastic Node
    """

    id = _JelAttrInt(read_only=True)
    envName = _JelAttrStr(read_only=True)
    intIP = _JelAttrIPv4(read_only=True)
    # "always guaranteed minimum"
    fixedCloudlets = _JelAttrInt()
    # "maximum"
    flexibleCloudlets = _JelAttrInt()

    def _update_from_dict(self, envName: str, node_from_env: Dict[str, Any]) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._node = node_from_env
        # Read-only attributes
        self._envName = envName
        for attr in ["id", "intIP"]:
            setattr(self, f"_{attr}", self._node[attr])

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

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._set_cloudlets()
