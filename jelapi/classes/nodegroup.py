import json
from enum import Enum
from typing import Any, Dict

from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import _JelasticObject, _JelAttrBool, _JelAttrList, _JelAttrStr


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
        for n in self.nodes:
            n.save()

    def __str__(self):
        """
        String representation
        """
        return f"JelasticNodeGroup {self.nodeGroup.value}"
