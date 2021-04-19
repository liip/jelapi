import warnings
from copy import deepcopy
from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes import (
    JelasticEnvironment,
    JelasticMountPoint,
    JelasticNodeGroup,
)
from jelapi.exceptions import JelasticObjectException
from jelapi.factories import JelasticNodeGroupFactory

from .utils import (
    get_standard_env,
    get_standard_mount_point,
    get_standard_node_group,
)

jelenv = JelasticEnvironment(jelastic_env=get_standard_env())


def test_JelasticNodeGroup_simple_load():
    """
    JelasticNodeGroup can be instantiated as-is
    """
    JelasticNodeGroup()


def test_JelasticNodeGroup_with_enough_data():
    """
    JelasticNodeGroup can be instantiated, deprecated format
    """
    with warnings.catch_warnings(record=True) as warns:
        # From API
        j1 = JelasticNodeGroup(
            parent=jelenv, node_group_from_env=get_standard_node_group()
        )
        assert j1.is_from_api
        assert len(warns) == 2

    with warnings.catch_warnings(record=True) as warns:
        j2 = JelasticNodeGroup(
            parent=jelenv,
            nodeGroup=JelasticNodeGroup.NodeGroupType.SQL_DATABASE,
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
    node_group = JelasticNodeGroupFactory()
    assert str(node_group) == "JelasticNodeGroup cp"

    with pytest.raises(AttributeError):
        #  nodeGroup cannot be changed to string
        node_group.nodeGroup = "sqldb"
    with pytest.raises(AttributeError):
        #  nodeGroup cannot be changed to enum either
        node_group.nodeGroup = JelasticNodeGroup.NodeGroupType.SQL_DATABASE


def test_JelasticNodeGroup_envVars_refreshes_from_API():
    """
    Getting the envVars gets us an API call
    """
    node_group = JelasticNodeGroupFactory()
    node_group.set_environment(JelasticEnvironment(jelastic_env=get_standard_env()))
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
    node_group.set_environment(jelenv)
    node_group._envVars = {"ID": "evil"}
    with pytest.raises(JelasticObjectException):
        node_group.save()


def test_JelasticNodeGroup_envVars_raises_if_set_empty():
    """
    Saving a faked envVars without fetch will raise
    """
    node_group = JelasticNodeGroupFactory()
    node_group.set_environment(JelasticEnvironment(jelastic_env=get_standard_env()))
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
        node_group.set_environment(jelenv_local)
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
    node_group.set_environment(JelasticEnvironment(jelastic_env=get_standard_env()))

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
    node_group.set_environment(JelasticEnvironment(jelastic_env=get_standard_env()))

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
    node_group.set_environment(JelasticEnvironment(jelastic_env=get_standard_env()))

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
    node_group.set_environment(JelasticEnvironment(jelastic_env=get_standard_env()))

    assert not node_group.differs_from_api()
    node_group.redeploy(docker_tag="latest")


def test_JelasticNodeGroup_read_file():
    """
    We can gather a single file in a nodegroup
    """
    node_group = JelasticNodeGroupFactory()
    node_group.set_environment(JelasticEnvironment(jelastic_env=get_standard_env()))

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
    node_group = JelasticNodeGroupFactory()
    node_group.set_environment(JelasticEnvironment(jelastic_env=get_standard_env()))

    assert not hasattr(node_group, "_mountPoints")
    jelapic()._ = Mock(
        return_value={"array": []},
    )
    assert node_group.mountPoints == []
    jelapic()._.assert_called_once()
    # Now assume it changed on the API
    jelapic()._ = Mock(
        return_value={"array": [get_standard_mount_point()]},
    )
    # It did not change, and the API was not called
    assert node_group.mountPoints == []
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
    cp_node_group = JelasticNodeGroupFactory()
    storage_node_group = JelasticNodeGroupFactory()

    jelenv = JelasticEnvironment(jelastic_env=get_standard_env())
    jelenv._nodeGroups = {"cp": cp_node_group, "storage": storage_node_group}
    cp_node_group.set_environment(jelenv)
    storage_node_group.set_environment(jelenv)

    jelapic()._ = Mock(
        return_value={"array": []},
    )
    cp_node_group.mountPoints.append(
        JelasticMountPoint(
            node_group=cp_node_group,
            name="test",
            path="/tmp/test",
            sourcePath="/srv",
            sourceNode=storage_node_group.nodes[0],
        )
    )
    # As we fetched, to append
    jelapic()._.assert_called_once()

    assert len(cp_node_group.mountPoints) == 1

    jelapic()._.reset_mock()
    cp_node_group.save()
    jelapic()._.assert_called_once()

    # Add another one, with the same path
    cp_node_group.mountPoints.append(
        JelasticMountPoint(
            node_group=cp_node_group,
            name="test2",
            path="/tmp/test",
            sourcePath="/srv/test2",
            sourceNode=storage_node_group.nodes[0],
        )
    )
    with pytest.raises(JelasticObjectException):
        cp_node_group.save()

    # Remove this one, sorry.
    del cp_node_group.mountPoints[1]
    # Remove the first one too
    del cp_node_group.mountPoints[0]

    # So the save will also remove the first one
    jelapic()._.reset_mock()
    cp_node_group.save()
    jelapic()._.assert_called_once()
