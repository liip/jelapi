import warnings
from copy import deepcopy
from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes import JelasticMountPoint, JelasticNodeGroup
from jelapi.exceptions import JelasticObjectException
from jelapi.factories import JelasticEnvironmentFactory, JelasticNodeGroupFactory

from .utils import (
    get_standard_mount_point,
    get_standard_node,
    get_standard_node_group,
)

jelenv = JelasticEnvironmentFactory()


def test_JelasticNodeGroup_simple_load():
    """
    JelasticNodeGroup can be instantiated as-is
    """
    JelasticNodeGroup()


def test_JelasticNodeGroup_no_api_call_unless_setup():
    """
    JelasticNodeGroup can be instantiated as-is
    """
    ng = JelasticNodeGroup()
    with pytest.raises(JelasticObjectException):
        ng.raise_unless_can_call_api()


def test_JelasticNodeGroup_with_enough_data():
    """
    JelasticNodeGroup can be instantiated, deprecated format
    """
    with warnings.catch_warnings(record=True) as warns:
        # From API
        j1 = JelasticNodeGroup(
            nodeGroupType=JelasticNodeGroup.NodeGroupType.APPLICATION_SERVER,
            parent=jelenv,
            node_group_from_env=get_standard_node_group(),
        )
        assert j1.is_from_api
        assert len(warns) == 2

    with warnings.catch_warnings(record=True) as warns:
        j2 = JelasticNodeGroup(
            parent=jelenv,
            nodeGroupType=JelasticNodeGroup.NodeGroupType.SQL_DATABASE,
        )
        assert not j2.is_from_api
        assert len(warns) == 1


def test_JelasticNodeGroup_with_missing_data():
    """
    JelasticNodeGroup cannot be instantiated with missing attributes
    """
    for musthavekey in ["name"]:
        nodegroup = get_standard_node_group()
        del nodegroup[musthavekey]
        ng = JelasticNodeGroup()
        with pytest.raises(KeyError):
            # missing name (alone) dies
            ng.update_from_env_dict(nodegroup)


def test_JelasticNodeGroup_factory():
    """
    Factory works
    """
    node_group = JelasticNodeGroupFactory()
    assert len(node_group.nodes) > 0
    assert node_group.is_from_api


def test_JelasticNodeGroup_immutable_data():
    """
    Doesn't differ from API at build
    """
    node_group = JelasticNodeGroupFactory(
        nodeGroupType=JelasticNodeGroup.NodeGroupType.APPLICATION_SERVER
    )
    assert str(node_group) == "JelasticNodeGroup cp"

    with pytest.raises(AttributeError):
        #  nodeGroup cannot be changed to string
        node_group.nodeGroupType = "sqldb"
    with pytest.raises(AttributeError):
        #  nodeGroup cannot be changed to enum either
        node_group.nodeGroupType = JelasticNodeGroup.NodeGroupType.SQL_DATABASE


def test_JelasticNodeGroup_envVars_refreshes_from_API():
    """
    Getting the envVars gets us an API call
    """
    node_group = JelasticNodeGroupFactory()
    assert node_group.nodeGroupType
    node_group.attach_to_environment(JelasticEnvironmentFactory())
    node_group.raise_unless_can_call_api()

    jelapic()._ = Mock(
        return_value={"object": {"VAR": "value"}},
    )
    assert "VAR" in node_group.envVars
    assert node_group.envVars["VAR"] == "value"
    # As we lazy-load, accessing the dict will call the API once
    jelapic()._.assert_called_once()
    assert not node_group.differs_from_api()


def test_JelasticNodeGroup_envVars_raises_if_set_without_fetch():
    """
    Saving a faked envVars without fetch will raise
    """
    node_group = JelasticNodeGroupFactory()
    node_group.attach_to_environment(jelenv)
    # Make sure they never were fetched
    node_group._envVars_need_fetching = True
    node_group._envVars = {"ID": "evil"}

    assert node_group._envVars != node_group._from_api["_envVars"]

    with pytest.raises(JelasticObjectException):
        node_group.save()


def test_JelasticNodeGroup_envVars_raises_if_set_empty():
    """
    Saving a faked envVars without fetch will raise
    """
    node_group = JelasticNodeGroupFactory()
    node_group.attach_to_environment(JelasticEnvironmentFactory())
    jelapic()._ = Mock(
        return_value={"object": {"VAR": "value"}},
    )
    # fetch it
    node_group.envVars
    # empty it
    node_group._envVars = {}
    with pytest.raises(JelasticObjectException):
        node_group.save()


def test_JelasticNodeGroup_envVars_raises_if_env_is_not_running():
    """
    Fetching envVars raises on envs not runnirg
    """
    from jelapi.classes import JelasticEnvironment

    JelStatus = JelasticEnvironment.Status
    for status in JelStatus:
        jelenv_local = deepcopy(jelenv)
        jelenv_local.status = status
        node_group = JelasticNodeGroupFactory()
        node_group.attach_to_environment(jelenv_local)
        jelapic()._ = Mock(
            return_value={"object": {"VAR": "value"}},
        )
        if status in [
            JelStatus.RUNNING,
            JelStatus.CREATING,
            JelStatus.CLONING,
        ]:
            node_group.envVars
        else:
            with pytest.raises(JelasticObjectException):
                node_group.envVars


def test_JelasticNodeGroup_envVars_updates():
    node_group = JelasticNodeGroupFactory()
    node_group.attach_to_environment(JelasticEnvironmentFactory())

    jelapic()._ = Mock(
        return_value={"object": {"VAR": "value"}},
    )
    assert node_group.envVars["VAR"] == "value"
    # As we lazy-load, accessing the dict will call the API once
    jelapic()._.assert_called_once()

    node_group.envVars["NEWVAR"] = "revolution"
    assert node_group.differs_from_api()
    jelapic()._ = Mock(return_value={"result": 0})
    # Save the addition, it will work, and call one set
    node_group.save()
    assert not node_group.differs_from_api()
    jelapic()._.assert_called_once()

    jelapic()._.reset_mock()
    del node_group.envVars["NEWVAR"]
    # Save the removal, it will work, and call one set
    node_group.save()
    jelapic()._.assert_called_once()
    assert not node_group.differs_from_api()

    # Now test both addition and removal, this will do a single "set"
    node_group.envVars["NEWVAR"] = "new"
    del node_group.envVars["VAR"]
    jelapic()._.reset_mock()
    node_group.save()
    jelapic()._.assert_called_once()
    assert not node_group.differs_from_api()


def test_JelasticNodeGroup_displayName_update():
    """
    Update displayName
    """
    node_group = JelasticNodeGroupFactory()
    node_group.attach_to_environment(JelasticEnvironmentFactory())

    assert not node_group.differs_from_api()
    node_group.displayName = "A new name for a new day"
    assert node_group.differs_from_api()

    jelapic()._ = Mock()
    node_group.save()
    assert not node_group.differs_from_api()
    jelapic()._.assert_called_once()


def test_JelasticNodeGroup_SLB_update():
    """
    Update SLB status
    """
    node_group = JelasticNodeGroupFactory()
    node_group.attach_to_environment(JelasticEnvironmentFactory())

    assert not node_group.differs_from_api()
    # Toggle the status
    node_group.isSLBAccessEnabled = not node_group.isSLBAccessEnabled
    assert node_group.differs_from_api()

    jelapic()._ = Mock()
    node_group.save()
    assert not node_group.differs_from_api()
    jelapic()._.assert_called_once()


def test_JelasticNodeGroup_redeploy():
    """
    NodeGroups can be redeployed
    """
    node_group = JelasticNodeGroupFactory()
    node_group.attach_to_environment(JelasticEnvironmentFactory())

    assert not node_group.differs_from_api()
    node_group.redeploy(docker_tag="latest")


def test_JelasticNodeGroup_read_file():
    """
    We can gather a single file in a nodegroup
    """
    node_group = JelasticNodeGroupFactory()
    node_group.attach_to_environment(JelasticEnvironmentFactory())

    jelapic()._ = Mock(
        return_value={
            "body": "Text content",
            "result": 0,
        },
    )
    with pytest.raises(TypeError):
        # We can't read no file
        node_group.read_file("")

    body = node_group.read_file("/tmp/test")
    jelapic()._.assert_called_once()
    assert body == "Text content"


def test_JelasticNodeGroup_get_mountPoints():
    """
    We can get the list of mountPoints
    """
    jelenv = JelasticEnvironmentFactory()
    node_group = jelenv.nodeGroups["cp"]

    assert node_group._mountPoints_need_fetching

    jelapic()._ = Mock(
        return_value={
            "array": [
                get_standard_mount_point(
                    source_node_id=jelenv.nodeGroups["storage"].nodes[0].id
                )
            ]
        },
    )
    assert len(node_group.mountPoints) == 1
    jelapic()._.assert_called_once()
    # Now assume it changed on the API
    jelapic()._ = Mock(
        return_value={"array": []},
    )
    # It did not change, and the API was not called
    assert node_group.mountPoints != []
    jelapic()._.assert_not_called()

    # There's no way to force-refresh, currently:
    with pytest.raises(TypeError):
        node_group._mountPoints = None
    node_group._mountPoints = []
    # It's still 0
    assert len(node_group.mountPoints) == 0
    jelapic()._.assert_not_called()


def test_JelasticNodeGroup_add_remove_mountPoints():
    """
    We can add mountPoints
    """
    # Instantiate a somewhat realistic environment
    cp_node_group = JelasticNodeGroupFactory(
        nodeGroupType=JelasticNodeGroup.NodeGroupType.APPLICATION_SERVER
    )
    storage_node_group = JelasticNodeGroupFactory(
        nodeGroupType=JelasticNodeGroup.NodeGroupType.SQL_DATABASE
    )

    jelenv = JelasticEnvironmentFactory()
    cp_node_group.attach_to_environment(jelenv)
    storage_node_group.attach_to_environment(jelenv)

    jelapic()._ = Mock(
        return_value={"array": []},
    )
    assert cp_node_group.mountPoints == []
    assert not cp_node_group._mountPoints_need_fetching

    # As we fetched, to append
    jelapic()._.assert_called_once()

    jmp = JelasticMountPoint(
        name="test",
        path="/tmp/test",
        sourcePath="/srv",
        sourceNode=storage_node_group.nodes[0],
    )
    jmp.attach_to_node_group(cp_node_group)
    assert not jmp.is_from_api

    assert len(cp_node_group.mountPoints) == 1

    jelapic()._.reset_mock()
    cp_node_group.save()
    jelapic()._.assert_called_once()
    # It made it "from API"
    assert jmp.is_from_api
    assert len(cp_node_group._from_api["_mountPoints"]) == 1
    assert cp_node_group._from_api["_mountPoints"][0].is_from_api

    # Add another one, with the same path
    jmp2 = JelasticMountPoint(
        name="test2",
        path="/tmp/test",
        sourcePath="/srv/test2",
        sourceNode=storage_node_group.nodes[0],
    )
    jmp2.attach_to_node_group(cp_node_group)
    assert not jmp2.is_from_api

    # It will override the previous one, so…
    assert len(cp_node_group.mountPoints) == 1

    # Saving shall work
    jelapic()._.reset_mock()
    cp_node_group.save()
    jelapic()._.assert_called_once()

    # Remove the only one
    del cp_node_group.mountPoints[0]
    assert len(cp_node_group.mountPoints) == 0
    assert len(cp_node_group._from_api["_mountPoints"]) == 1
    assert cp_node_group._from_api["_mountPoints"][0].is_from_api

    # So the save will also remove the first one
    jelapic()._.reset_mock()
    cp_node_group.save()
    jelapic()._.assert_called_once()


def test_JelasticNodeGroup_links():
    """
    Getting the links works without further ado
    """
    ng = JelasticNodeGroupFactory()
    assert len(ng.links) == 0


def test_JelasticNodeGroup_links_cannot_be_fetched_without_nodes():
    """
    Getting the links doesn't work without nodes
    """
    ng = JelasticNodeGroupFactory()
    ng.nodes = []
    with pytest.raises(JelasticObjectException):
        ng.links


def test_JelasticNodeGroup_adding_links_means_topology_change():
    """
    Getting the links doesn't work without nodes
    """
    cpng = JelasticNodeGroupFactory(
        nodeGroupType=JelasticNodeGroup.NodeGroupType.APPLICATION_SERVER
    )
    sqldbng = JelasticNodeGroupFactory(
        nodeGroupType=JelasticNodeGroup.NodeGroupType.SQL_DATABASE
    )
    cpng.attach_to_environment(jelenv)
    sqldbng.attach_to_environment(jelenv)
    assert len(cpng.links) == 0

    cpng.links["SQLDB"] = JelasticNodeGroup.NodeGroupType.SQL_DATABASE
    assert len(cpng.links) == 1
    assert cpng.needs_topology_update()


def test_JelasticNodeGroup_links_non_empty():
    """
    Getting the links works with a node that has a link
    """
    jelenv = JelasticEnvironmentFactory()
    cpng = jelenv.nodeGroups["cp"]
    sqldbng = jelenv.nodeGroups["sqldb"]

    ndict = get_standard_node()
    ndict["id"] = cpng.nodes[0].id

    ndict["customitem"] = {
        "dockerLinks": [
            {"type": "IN", "sourceNodeId": sqldbng.nodes[0].id, "alias": "SQLDB"},
            {"type": "OUT", "sourceNodeId": 154},
        ]
    }
    cpng.nodes[0].update_from_env_dict(ndict)

    assert len(cpng.links) == 1
    assert "SQLDB" in cpng.links
    assert cpng.links["SQLDB"] == JelasticNodeGroup.NodeGroupType.SQL_DATABASE


def test_JelasticNodeGroup_containerVolumes():
    """
    Get container volumes
    """
    ng = JelasticNodeGroupFactory()
    ng.attach_to_environment(jelenv)

    ng._mountPoints_need_fetching = False
    ng._mountPoints = []

    jelapic()._ = Mock(
        return_value={"object": ["/tmp/volume1", "/tmp/volume2"]},
    )
    assert len(ng.containerVolumes) == 2
    assert jelapic()._.called_once()


def test_JelasticNodeGroup_containerVolumes_add_remove():
    """
    Get container volumes
    """
    ng = JelasticNodeGroupFactory()
    ng.attach_to_environment(jelenv)

    ng._mountPoints_need_fetching = False
    ng._mountPoints = []

    ng.copy_self_as_from_api("_mountPoints")
    ng._containerVolumes = ["/tmp/volume1", "/tmp/volume2"]
    ng.copy_self_as_from_api("_containerVolumes")

    ng.containerVolumes.append("/srv")
    assert ng.differs_from_api()

    jelapic()._ = Mock()
    ng.save()
    # There was one add
    jelapic()._.assert_called_once()
    assert not ng.differs_from_api()
    assert len(ng.containerVolumes) == 3

    del ng.containerVolumes[2]
    assert len(ng.containerVolumes) == 2

    jelapic()._.reset_mock()
    ng.save()
    # There was one removal
    jelapic()._.assert_called_once()
    assert not ng.differs_from_api()
    assert len(ng.containerVolumes) == len(ng._containerVolumes) == 2

    #  Add an identical
    ng.containerVolumes.append(ng.containerVolumes[0])
    with pytest.raises(JelasticObjectException):
        ng.save()


def test_JelasticNodeGroup_topology_without_nodes():
    """
    These fail, we need the node for lots of information
    """
    ng = JelasticNodeGroupFactory()
    ng.nodes = []
    with pytest.raises(JelasticObjectException):
        ng.get_topology()


def test_JelasticNodeGroup_topology():
    """
    Get a full'er topology
    """
    jelenv = JelasticEnvironmentFactory()
    cp_node_group = jelenv.nodeGroups["cp"]

    cp_node_group.links["SQLDB"] = JelasticNodeGroup.NodeGroupType.SQL_DATABASE
    cp_node_group.nodes[0].docker_registry = {"url": "https://docker.example.com/"}
    cp_node_group.nodes[0].docker_image = "example_image:tag"
    assert len(cp_node_group.nodes) > 0

    cp_node_group._envVars_need_fetching = False
    cp_node_group.envVars["HOSTNAME"] = "https://example.com"

    # Now get it
    topology = cp_node_group.get_topology()
    assert topology["count"] == len(cp_node_group.nodes)
    # Check that the links' syntax got computed correctly
    assert topology["links"] == ["sqldb:SQLDB"]

    cp_node_group.links["BROKEN"] = "sqldb"
    with pytest.raises(TypeError):
        cp_node_group.get_topology()


def test_JelasticNodeGroup_duplicate_mountPoints():
    """
    Test we can't save duplicated mount points
    """
    j = JelasticEnvironmentFactory()
    cpng = j.nodeGroups["cp"]

    # Assume they got fetched
    cpng._mountPoints_need_fetching = False
    # Attach one.
    mount = JelasticMountPoint(
        name="Test",
        path="/srv",
        sourceNode=j.nodeGroups["storage"].nodes[0],
        sourcePath="/srv/src",
    )
    mount.attach_to_node_group(cpng)
    assert len(cpng.mountPoints) == 1

    # Now pretend to add another one, but cheat
    cpng.mountPoints.append(mount)

    with pytest.raises(JelasticObjectException):
        cpng._save_mount_points()


def test_JelasticNodeGroup_copy_from_api():
    """
    Can we copy a nodeGroup
    """
    j = JelasticEnvironmentFactory()
    cpng = j.nodeGroups["cp"]

    # Let's assume they were fetched
    cpng._mountPoints_need_fetching = False
    cpng._containerVolumes_need_fetching = False
    cpng._envVars_need_fetching = False

    assert cpng.is_from_api
    cpng2 = cpng.archive_from_api()
    assert not cpng2.is_from_api
