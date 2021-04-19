from ..exceptions import deprecation
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import _JelasticObject, _JelAttrBool, _JelAttrStr
from .nodegroup import JelasticNodeGroup


class _JelasticVolume(_JelasticObject):
    """
    Represents a Jelastic Volume (CountainerVolume or MountPoint)
    """

    # 'parent'
    nodeGroup = _JelAttr(read_only=True, checked_for_differences=False)

    # Whether it was from the API or not
    is_new = _JelAttrBool()

    # Source nodeGroup / Where it is mounted _to_
    name = _JelAttrStr(read_only=True)
    path = _JelAttrStr(read_only=True)

    def __init__(
        self,
        *,
        node_group: JelasticNodeGroup = None,
        name: str = None,
        path: str = None,
    ) -> None:
        """
        Construct a _JelasticVolume from basic stuff
        """
        super().__init__()

        if node_group:
            deprecation(
                "_Volume.__init__(): Passing node_group is deprecated; use attach_to_node_group instead",
            )
            self.attach_to_node_group(node_group)

        self._name = name
        self._path = path
        self.is_new = True
        assert self.differs_from_api

    def attach_to_node_group(self, node_group: JelasticNodeGroup) -> None:
        """
        Connect node_group to mountPoint, and inversely
        """

        node_group.append_mount_point(self)

        self._envName = self._nodeGroup._parent.envName

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        # TODO

    def __str__(self):
        """
        String representation
        """
        return f"_JelasticVolume {self.path} on {self.nodeGroup}"
