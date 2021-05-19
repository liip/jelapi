import json
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List

from ..exceptions import JelasticObjectException, deprecation
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import (
    _JelasticObject,
    _JelAttrBool,
    _JelAttrDict,
    _JelAttrInt,
    _JelAttrList,
    _JelAttrStr,
)

if TYPE_CHECKING:  # pragma: no cover
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

    nodeGroupType = _JelAttr(read_only=True)
    envName = _JelAttrStr(read_only=True)

    isSLBAccessEnabled = _JelAttrBool()
    displayName = _JelAttrStr()
    nodes = _JelAttrList(checked_for_differences=False)

    # Variables
    _envVars = (
        _JelAttrDict()
    )  # this is the JelAttr, use envVars to access them through lazy loading
    _envVars_need_fetching = _JelAttrBool(checked_for_differences=False)

    _mountPoints = _JelAttrList(
        checked_for_differences=False
    )  # this is the JelAttr, use mountPoints to access them through lazy loading
    # Boolean flag to help lazy-load
    _mountPoints_need_fetching = _JelAttrBool(checked_for_differences=False)

    _containerVolumes = (
        _JelAttrList()
    )  # this is the JelAttr, use containerVolumes to access them through lazy loading
    # Boolean flag to help lazy-load
    _containerVolumes_need_fetching = _JelAttrBool(checked_for_differences=False)

    _links = (
        _JelAttrDict()
    )  # this is the JelAttr, use links to access them through lazy loading

    # in Gb
    diskLimit = _JelAttrInt()

    @property
    def envVars(self):
        """
        Lazy load envVars when they're accessed
        """
        from .environment import JelasticEnvironment

        JelStatus = JelasticEnvironment.Status

        if hasattr(self, "_parent") and self._parent.status not in [
            JelStatus.RUNNING,
            JelStatus.CREATING,
            JelStatus.CLONING,
        ]:
            raise JelasticObjectException(
                "envVars cannot be gathered on environments not running"
            )
        if self._envVars_need_fetching:
            self.raise_unless_can_call_api()

            response = self.api._(
                "Environment.Control.GetContainerEnvVarsByGroup",
                envName=self.envName,
                nodeGroup=self.nodeGroupType.value,
            )
            self._envVars = response["object"]
            self._envVars_need_fetching = False
            self.copy_self_as_from_api("_envVars")
        return self._envVars

    def _set_env_vars(self):
        """
        Set the modified envVars
        """
        # Only set them if they were fetched first
        if self._envVars_need_fetching:
            if self._envVars != {}:
                raise JelasticObjectException(
                    "envVars cannot be saved if not fetched first (no blind set)"
                )
        else:
            if len(self._envVars) == 0 and len(self._from_api["_envVars"]) > 0:
                raise JelasticObjectException(
                    "envVars cannot be set to empty (no wipe out)"
                )
            if self._from_api["_envVars"] != self._envVars:
                self.raise_unless_can_call_api()
                self.api._(
                    "Environment.Control.SetContainerEnvVarsByGroup",
                    envName=self.envName,
                    nodeGroup=self.nodeGroupType.value,
                    data=json.dumps(self._envVars),
                )
                self.copy_self_as_from_api("_envVars")

    @property
    def mountPoints(self) -> List["JelasticMountPoint"]:
        """
        Lazy load mountPoints when they're accessed
        """
        self.raise_unless_can_call_api()

        # from .environment import JelasticEnvironment
        from .mountpoint import JelasticMountPoint

        # JelStatus = JelasticEnvironment.Status
        #
        # if self._parent.status not in [
        #     JelStatus.RUNNING,
        #     JelStatus.CREATING,
        #     JelStatus.CLONING,
        # ]:
        #     raise JelasticObjectException(
        #         "envVars cannot be gathered on environments not running"
        #     )
        if self._mountPoints_need_fetching:
            response = self.api._(
                "Environment.File.GetMountPoints",
                envName=self.envName,
                nodeGroup=self.nodeGroupType.value,
            )

            for mpdict in response["array"]:
                mp = JelasticMountPoint()
                mp.attach_to_node_group(self)
                mp.update_from_env_dict(mpdict)

            self._mountPoints_need_fetching = False
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
                        self._links[link["alias"]] = node_group.nodeGroupType
                        break
            self.copy_self_as_from_api("_links")

        return self._links

    def _save_mount_points(self):
        """
        Verify that the mount points have not changed, apply the changes
        """
        # Only check them if they were accessed
        if not self._mountPoints_need_fetching:
            mountpaths = [m.path for m in self.mountPoints]
            if len(set(mountpaths)) != len(mountpaths):
                raise JelasticObjectException(
                    f"Duplicate MountPoints won't work {','.join(mountpaths)}"
                )
            # Delete the obsolete mountpaths
            for mp in self._from_api.get("_mountPoints", []):
                if mp.path not in mountpaths:
                    mp.del_from_api()
                mp.save()

            # Create the new mountpaths
            for mp in self.mountPoints:
                if not mp.is_from_api:
                    mp.add_to_api()
                mp.save()
                assert not mp.differs_from_api()

            for mp in self.mountPoints:
                mp.copy_self_as_from_api()

        self.copy_self_as_from_api("_mountPoints")
        for mp in self._from_api.get("_mountPoints", []):
            mp.copy_self_as_from_api()

    @property
    def containerVolumes(self) -> List[str]:
        """
        Lazy load containerVolumes when they're accessed
        """
        self.raise_unless_can_call_api()

        if self._containerVolumes_need_fetching:
            response = self.api._(
                "Environment.Control.GetContainerVolumesByGroup",
                envName=self.envName,
                nodeGroup=self.nodeGroupType.value,
            )
            # We need to exclude the mountPoints
            self._containerVolumes = [
                cv
                for cv in response["object"]
                if cv not in [mp.path for mp in self.mountPoints]
            ]
            self._containerVolumes_need_fetching = False
            self.copy_self_as_from_api("_containerVolumes")
        return self._containerVolumes

    def _save_container_volumes(self):
        """
        Verify that the container volumes have not changed, apply the changes
        """
        self.raise_unless_can_call_api()

        # Only check them if they were accessed
        if not self._containerVolumes_need_fetching:
            if len(set(self.containerVolumes)) != len(self.containerVolumes):
                raise JelasticObjectException(
                    f"Duplicate Container Volumes won't work {','.join(self.containerVolumes)}"
                )
            # Delete the obsolete containerVolumes
            toremove = [
                cv
                for cv in self._from_api.get("_containerVolumes", [])
                if cv not in self.containerVolumes
            ]
            if len(toremove) > 0:
                self.api._(
                    "Environment.Control.RemoveContainerVolumes",
                    envName=self.envName,
                    nodeGroup=self.nodeGroupType.value,
                    volumes=json.dumps(toremove),
                )

            # Create the new mountpaths
            toadd = [
                cv
                for cv in self.containerVolumes
                if cv not in self._from_api.get("_containerVolumes", [])
            ]
            if len(toadd) > 0:
                self.api._(
                    "Environment.Control.AddContainerVolumes",
                    envName=self.envName,
                    nodeGroup=self.nodeGroupType.value,
                    volumes=json.dumps(toadd),
                )
            self.copy_self_as_from_api("_containerVolumes")

    def get_topology(self) -> Dict[str, Any]:
        """
        Return the "NodeGroup / Nodes" topology, as consumed by ChangeTopology
        """
        if len(self.nodes) == 0:
            raise JelasticObjectException("Can't get topology for an empty nodeGroup")
        node0 = self.nodes[0]
        topology = {
            "count": len(self.nodes),
            "restartDelay": 0,
            "displayName": self.displayName,
            "isSLBAccessEnabled": self.isSLBAccessEnabled,
            "nodeGroup": self.nodeGroupType.value,
            "nodeType": node0.nodeType.value,
            "diskLimit": self.diskLimit,
            "mission": node0.nodemission,
            "fixedCloudlets": node0.fixedCloudlets,
            "flexibleCloudlets": node0.flexibleCloudlets,
        }
        from .node import JelasticNode

        if node0.nodeType == JelasticNode.NodeType.DOCKER:
            if hasattr(node0, "docker_registry"):
                topology["registry"] = node0.docker_registry

            if hasattr(node0, "docker_image") and node0.docker_image:
                topology["image"] = node0.docker_image

        # The important links
        links = []
        for key, ngtype in self.links.items():
            if not isinstance(ngtype, self.NodeGroupType):
                raise TypeError(
                    f"Links' values must be of type NodeGroupType ({ngtype})"
                )
            # Find the correct node_group value ("storage" or "sqldb") in the parent's
            node_group = next(
                (
                    ng.nodeGroupType.value
                    for ng in self._parent.nodeGroups.values()
                    if ng.nodeGroupType == ngtype
                ),
            )
            links.append(f"{node_group}:{key}")

        if links:
            topology["links"] = links

        # The environment variables, if we got them.
        if not self._envVars_need_fetching:
            if self._envVars:
                topology["env"] = self._envVars
        return topology

    def needs_topology_update(self) -> bool:
        """
        Whether the ng needs a topology update from the environment
        """
        if self.nodes and self._from_api["diskLimit"] != self.diskLimit:
            return True
        if not hasattr(self, "_links"):
            # Never fetched, no need
            return False
        return self._from_api["_links"] != self._links

    def append_node(self, node: "JelasticNode") -> None:
        """
        Called from node, allow to append a node to our list
        """
        self.nodes.append(node)
        node._nodeGroup = self
        # Update nodeGroup-level attributes
        if len(self.nodes) == 1:
            # In node's API, diskLimit is given in bytes, but topology update, and at nodeGroup level, we store it as Gb
            self.diskLimit = int(node.diskLimit / 1000)
            self.copy_self_as_from_api("diskLimit")

    def append_mount_point(self, mount_point: "JelasticMountPoint") -> None:
        """
        Called from mount_point, allow to append a mountPoint to our list
        """
        # Assume we want to force this one
        for mp in self._mountPoints:
            if mp.path == mount_point.path:
                self._mountPoints.remove(mp)
        self._mountPoints.append(mount_point)
        mount_point._nodeGroup = self

    def attach_to_environment(self, environment: "JelasticEnvironment") -> None:
        """
        Set the parent environment, if nodeGroup is correctly setup
        """
        # Make sure the parent also has this nodeGroup listed
        if hasattr(self, "nodeGroupType"):
            self._parent = environment

            environment.attach_node_group(self)

            # Read-only attributes
            self._envName = self._parent.envName

    def update_from_env_dict(self, node_group_from_env: Dict[str, Any]) -> None:
        """
        Construct/Update our object from the structure
        """
        # Allow exploration of the returned object, but don't act on it.
        self._node_group = node_group_from_env

        self._nodeGroupType = next(
            (ng for ng in self.NodeGroupType if ng.value == self._node_group["name"]),
        )

        # R/W attributes
        self._displayName = self._node_group.get(
            "displayName", ""
        )  # Apparently optional
        self._isSLBAccessEnabled = self._node_group.get("isSLBAccessEnabled")

        # These two need fetching now (it was from API)
        self._mountPoints_need_fetching = True
        self._containerVolumes_need_fetching = True
        self._envVars_need_fetching = True

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def raise_unless_can_call_api(self):
        """
        Check if we can update to API, or raise
        """
        if not hasattr(self, "envName") or not hasattr(self, "nodeGroupType"):
            raise JelasticObjectException(
                "Cannot update to API, use attach_to_environment() before saving!"
            )

    def __init__(
        self,
        *,
        parent: "JelasticEnvironment" = None,
        node_group_from_env: Dict[str, Any] = None,
        nodeGroupType: NodeGroupType = None,
    ) -> None:
        """
        Construct a JelasticNodeGroup from the outer data
        """
        super().__init__()

        # Instantiate some empty, or default
        self._displayName = ""
        self._isSLBAccessEnabled = False

        self.nodes = []
        self._mountPoints = []
        self._mountPoints_need_fetching = False
        self._containerVolumes = []
        self._containerVolumes_need_fetching = False

        self._envVars = {}
        self._envVars_need_fetching = False

        if nodeGroupType:
            # Construct a node Group out of the blue
            self._nodeGroupType = nodeGroupType

            if parent:
                deprecation(
                    "NodeGroup.__init__(): Passing parent is deprecated; use attach_to_environment instead",
                )
                self.attach_to_environment(parent)
                assert self._parent == parent

        if node_group_from_env:
            deprecation(
                "NodeGroup.__init__(): Passing node_group_from_env is deprecated; use update_from_env_dict instead",
            )
            self.update_from_env_dict(node_group_from_env=node_group_from_env)
            assert self.is_from_api

    def before_archive_from_api(self):
        """
        When archiving from API, fetch mountPoints, containerVolumes and envVars
        """
        self.mountPoints
        self.containerVolumes
        self.envVars

    def _apply_data(self):
        """
        Use "ApplyData" to save all the data we _can_ save
        """
        self.raise_unless_can_call_api()

        #  Prepare data attr for ApplyData call
        data = {}
        for attr in ["displayName"]:
            v = getattr(self, attr)
            if attr not in self._from_api or self._from_api[attr] != v:
                data[attr] = v
        if len(data) > 0:
            # Jelastic API 6.0
            self.api._(
                "Environment.NodeGroup.ApplyData",
                envName=self.envName,
                nodeGroup=self.nodeGroupType.value,
                data=json.dumps(data),
            )
            for k in data.keys():
                self._from_api[k] = data[k]

    def _slb_access(self):
        """
        Use "SetSLBAccessEnabled" to set it
        """
        self.raise_unless_can_call_api()

        if (
            "isSLBAccessEnabled" not in self._from_api
            or self._from_api["isSLBAccessEnabled"] != self.isSLBAccessEnabled
        ):
            # Jelastic API 6.0
            self.api._(
                "Environment.NodeGroup.SetSLBAccessEnabled",
                envName=self.envName,
                nodeGroup=self.nodeGroupType.value,
                enabled=self.isSLBAccessEnabled,
            )
            self._from_api["isSLBAccessEnabled"] = self.isSLBAccessEnabled

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._apply_data()
        self._slb_access()
        self._set_env_vars()
        for n in self.nodes:
            n.save()
        self.copy_self_as_from_api("nodes")
        self._save_container_volumes()
        self._save_mount_points()

    def __str__(self) -> str:
        """
        String representation
        """
        return f"JelasticNodeGroup {self.nodeGroupType.value}"

    # Jelastic-related utilites
    def read_file(self, path: str) -> str:
        """
        Read a file in a nodeGroup
        """
        self.raise_unless_can_call_api()

        if not path:
            raise TypeError(f"path {path} cannot be empty")

        from .environment import JelasticEnvironment

        if self._parent.status != JelasticEnvironment.Status.RUNNING:
            raise JelasticObjectException(
                "Files cannot be read from environments not running."
            )
        response = self.api._(
            "Environment.File.Read",
            envName=self.envName,
            nodeGroup=self.nodeGroupType.value,
            path=path,
        )
        return response["body"]

    def redeploy(self, docker_tag: str = "latest"):
        """
        Redeploy a nodeGroup to a certain docker tag
        """
        self.raise_unless_can_call_api()

        self.api._(
            "Environment.Control.RedeployContainersByGroup",
            envName=self.envName,
            nodeGroup=self.nodeGroupType.value,
            tag=docker_tag,
        )
