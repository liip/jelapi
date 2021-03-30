from typing import Any, Dict

from ..exceptions import JelasticObjectException
from ._volume import _JelasticVolume
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import _JelAttrStr
from .node import JelasticNode
from .nodegroup import JelasticNodeGroup


class JelasticMountPoint(_JelasticVolume):
    """
    Represents a Jelastic MountPoint, a mount link between nodes
    """

    # Where it is mounted _from_
    sourceNode = _JelAttr(read_only=True)
    sourcePath = _JelAttrStr(read_only=True)

    def _update_from_dict(self, mount_point_from_api: Dict[str, Any]) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._mount_point = mount_point_from_api

        # Set the name and path in _JelasticVolume
        self._name = self._mount_point["name"]
        self._path = self._mount_point["path"]

        self._sourcePath = self._mount_point["sourcePath"]

        # Now find internal source node
        source_node_id = int(self._mount_point["sourceNodeId"])

        for ng in self._nodeGroup._parent.nodeGroups.values():
            for node in ng.nodes:
                if node.id == source_node_id:
                    self._sourceNode = node

        if not hasattr(self, "_sourceNode"):
            raise JelasticObjectException(
                f"Didn't find node id {source_node_id} in environment"
            )

        self.is_new = False
        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __init__(
        self,
        *,
        node_group: JelasticNodeGroup = None,
        mount_point_from_api: Dict[str, Any] = None,
        name: str = None,
        path: str = None,
        sourceNode: JelasticNode = None,
        sourcePath: str = None,
    ) -> None:
        """
        Construct a JelasticMountPoint from the outer data
        """
        if not node_group:
            raise JelasticObjectException("node_group is mandatory for init")
        if mount_point_from_api:
            super().__init__(node_group=node_group)
            self._update_from_dict(mount_point_from_api=mount_point_from_api)
            assert not self.differs_from_api()

        elif name and path and sourceNode and sourcePath:
            # IF we create a new JelasticMountPoint
            super().__init__(node_group=node_group, name=name, path=path)
            # These go in RO attributes
            self._sourceNode = sourceNode
            self._sourcePath = sourcePath
            assert not self.is_from_api
            assert self.differs_from_api()

    def add_to_api(self) -> None:
        """
        Push this mountpoint to API
        """
        if self.is_from_api:
            raise JelasticObjectException(
                "MountPoint cannot be added to API, it came from it"
            )
        # Needs to be added
        self.api._(
            "Environment.File.AddMountPointByGroup",
            envName=self._envName,
            nodeGroup=self._nodeGroup.nodeGroup.value,
            path=self.path,
            sourceNodeId=self.sourceNode.id,
            sourcePath=self.sourcePath,
        )
        self.copy_self_as_from_api()
        assert not self.differs_from_api()

    def del_from_api(self) -> None:
        """
        Delete this mountpoint from API
        """
        if not self.is_from_api:
            raise JelasticObjectException(
                "MountPoint cannot be removed from API, as it did not come from it"
            )
        # Needs to be removed
        self.api._(
            "Environment.File.RemoveMountPointByGroup",
            envName=self._envName,
            nodeGroup=self._nodeGroup.nodeGroup.value,
            path=self.path,
        )
        self.copy_self_as_from_api()
        assert not self.differs_from_api()

    def refresh_from_api(self) -> None:
        """
        JelasticMountPoints could be refreshed by themselves
        """
        # TODO

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        # TODO

    def __str__(self):
        """
        String representation
        """
        return f"JelasticMountPount {self.path} on {self.nodeGroup} - from {self.sourcePath} on {self.sourceNode.id}"
