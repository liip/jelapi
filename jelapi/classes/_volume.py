from ..exceptions import JelasticObjectException
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
        if not node_group:
            raise JelasticObjectException("node_group is mandatory for init")

        self._nodeGroup = node_group
        self._envName = self._nodeGroup._parent.envName
        self._name = name
        self._path = path
        self.is_new = True
        assert self.differs_from_api

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
        return f"_JelasticVolume {self.path} on {self.nodeGroup}"
