import json
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List

from ..exceptions import JelasticObjectException
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import (
    _JelasticObject,
    _JelAttrBool,
    _JelAttrDict,
    _JelAttrList,
    _JelAttrStr,
)

if TYPE_CHECKING:
    from .environment import JelasticEnvironment
    from .mountpoint import JelasticMountPoint
    from .node import JelasticNode


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

    _mountPoints = _JelAttrList(
        checked_for_differences=False
    )  # this is the JelAttr, use mountPoints to access them through lazy loading

    _containerVolumes = (
        _JelAttrList()
    )  # this is the JelAttr, use containerVolumes to access them through lazy loading

    _links = (
        _JelAttrDict()
    )  # this is the JelAttr, use links to access them through lazy loading

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

    @property
    def mountPoints(self) -> List["JelasticMountPoint"]:
        """
        Lazy load mountPoints when they're accessed
        """
        from .mountpoint import JelasticMountPoint

        if not hasattr(self, "_mountPoints"):
            response = self.api._(
                "Environment.File.GetMountPoints",
                envName=self.envName,
                nodeGroup=self.nodeGroup.value,
            )
            self._mountPoints = [
                JelasticMountPoint(node_group=self, mount_point_from_api=mp)
                for mp in response["array"]
            ]
            self.copy_self_as_from_api("_mountPoints")
        return self._mountPoints

    @property
    def links(self) -> Dict[str, NodeGroupType]:
        """
        "IN"wards links dict {"key": ng}
        """
        if len(self.nodes) == 0:
            raise JelasticObjectException("Links can't be fetched without nodes")
        if not hasattr(self, "_links"):
            self._links = {}
            for link in self.nodes[0].links:
                for node_group in self._parent.nodeGroups.values():
                    if link["sourceNodeId"] in [n.id for n in node_group.nodes]:
                        self._links[link["alias"]] = node_group.nodeGroup
                        break
            self.copy_self_as_from_api("_links")

        return self._links

    def _save_mount_points(self):
        """
        Verify that the mount points have not changed, apply the changes
        """
        # Only check them if they were accessed
        if hasattr(self, "_mountPoints"):
            mountpaths = [m.path for m in self.mountPoints]
            if len(set(mountpaths)) != len(mountpaths):
                raise JelasticObjectException(
                    f"Duplicate MountPoints won't work {','.join(mountpaths)}"
                )
            # Delete the obsolete mountpaths
            for mp in self._from_api["_mountPoints"]:
                if mp.path not in mountpaths:
                    mp.del_from_api()
                mp.save()

            # Create the new mountpaths
            for mp in self.mountPoints:
                if not mp.is_from_api:
                    mp.add_to_api()
                mp.save()
                assert not mp.differs_from_api()

            self.copy_self_as_from_api("_mountPoints")

    @property
    def containerVolumes(self) -> List[str]:
        """
        Lazy load containerVolumes when they're accessed
        """

        if not hasattr(self, "_containerVolumes"):
            response = self.api._(
                "Environment.Control.GetContainerVolumesByGroup",
                envName=self.envName,
                nodeGroup=self.nodeGroup.value,
            )
            # We need to exclude the mountPoints
            self._containerVolumes = [
                cv
                for cv in response["object"]
                if cv not in [mp.path for mp in self.mountPoints]
            ]
            self.copy_self_as_from_api("_containerVolumes")
        return self._containerVolumes

    def _save_container_volumes(self):
        """
        Verify that the container volumes have not changed, apply the changes
        """
        # Only check them if they were accessed
        if hasattr(self, "_containerVolumes"):
            if len(set(self.containerVolumes)) != len(self.containerVolumes):
                raise JelasticObjectException(
                    f"Duplicate Container Volumes won't work {','.join(self.containerVolumes)}"
                )
            # Delete the obsolete containerVolumes
            toremove = [
                cv
                for cv in self._from_api["_containerVolumes"]
                if cv not in self.containerVolumes
            ]
            if len(toremove) > 0:
                self.api._(
                    "Environment.Control.RemoveContainerVolumes",
                    envName=self.envName,
                    nodeGroup=self.nodeGroup.value,
                    volumes=json.dumps(toremove),
                )

            # Create the new mountpaths
            toadd = [
                cv
                for cv in self.containerVolumes
                if cv not in self._from_api["_containerVolumes"]
            ]
            if len(toadd) > 0:
                self.api._(
                    "Environment.Control.AddContainerVolumes",
                    envName=self.envName,
                    nodeGroup=self.nodeGroup.value,
                    volumes=json.dumps(toadd),
                )
            self.copy_self_as_from_api("_containerVolumes")

    def get_topology(self) -> Dict[str, Any]:
        """
        Return the "NodeGroup / Nodes" topology, as consumed by ChangeTopology
        """
        if len(self.nodes) == 0:
            raise JelasticObjectException("Can't get topology for an empty nodeGroup")
        # return {"count": , "restartDelay": 0, "nod"}
        node0 = self.nodes[0]
        topology = {
            "count": len(self.nodes),
            "restartDelay": 0,
            "displayName": self.displayName,
            "nodeGroup": self.nodeGroup.value,
            "nodeType": node0.nodeType.value,
            "mission": node0.nodemission,
            "fixedCloudlets": node0.fixedCloudlets,
            "flexibleCloudlets": node0.flexibleCloudlets,
        }
        from .node import JelasticNode

        if node0.nodeType == JelasticNode.NodeType.DOCKER:
            if hasattr(node0, "docker_registry"):
                topology["registry"] = {"url": node0.docker_registry["url"]}
                topology["docker"] = {
                    "registry": node0.docker_registry,
                    "image": node0.docker_image,
                }

            # The important links
            topology["links"] = []
            for key, ngtype in self.links.items():
                if not isinstance(ngtype, self.NodeGroupType):
                    raise TypeError(
                        f"Links' values must be of type NodeGroupType ({ngtype})"
                    )
                # Find the correct node_group value ("storage" or "sqldb") in the parent's
                node_group = next(
                    (
                        ng.nodeGroup.value
                        for ng in self._parent.nodeGroups.values()
                        if ng.nodeGroup == ngtype
                    ),
                )
                topology["links"].append(f"{node_group}:{key}")
        return topology

    def needs_topology_update(self):
        """
        Whether the ng needs a topology update from the environment
        """
        if not hasattr(self, "_links"):
            # Never fetched, no need
            return False
        return self._from_api["_links"] != self._links

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

    def __init__(
        self,
        *,
        parent: "JelasticEnvironment",
        node_group_from_env: Dict[str, Any] = None,
        nodeGroup: NodeGroupType = None,
        nodeType: "JelasticNode.NodeType" = None,
    ) -> None:
        """
        Construct a JelasticNodeGroup from the outer data
        """
        super().__init__()
        if node_group_from_env:
            self._update_from_dict(
                parent=parent, node_group_from_env=node_group_from_env
            )
        elif nodeGroup and nodeType:
            # Construct a node Group out of the blue
            self._parent = parent
            self._nodeGroup = nodeGroup
            self._envName = self._parent.envName
            # Instantiate the rest empty, or default
            self._displayName = ""
            self._isSLBAccessEnabled = False
            # Instantiate with one node
            from .node import JelasticNode

            self.nodes = [JelasticNode(node_group=self, nodeType=nodeType)]
        else:
            raise TypeError(
                "NodeGroup instantiation needs either node_group_from_env or (nodeGroup, nodeType)"
            )

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
        self.copy_self_as_from_api("nodes")
        self._save_container_volumes()
        self._save_mount_points()

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
