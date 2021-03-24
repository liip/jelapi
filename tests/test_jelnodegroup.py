from copy import deepcopy
from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes import JelasticEnvironment, JelasticNode, JelasticNodeGroup
from jelapi.exceptions import JelasticObjectException

from .utils import get_standard_env, get_standard_node_group

jelenv = JelasticEnvironment(jelastic_env=get_standard_env())


def test_JelasticNodeGroup_with_enough_data():
    """
    JelasticNodeGroup can be instantiated
    """
    JelasticNodeGroup(parent=jelenv, node_group_from_env=get_standard_node_group())


def test_JelasticNodeGroup_with_missing_data():
    """
    JelasticNodeGroup cannot be instantiated with missing attributes
    """
    with pytest.raises(TypeError):
        # parent is mandatory
        JelasticNode(node_group_from_env=get_standard_node_group())
    with pytest.raises(TypeError):
        # node_group_from_env is also mandatory
        JelasticNode(parent=jelenv)

    for musthavekey in ["name"]:
        nodegroup = get_standard_node_group()
        del nodegroup[musthavekey]
        with pytest.raises(KeyError):
            # missing id Dies
            JelasticNodeGroup(parent=jelenv, node_group_from_env=nodegroup)


def test_JelasticNodeGroup_immutable_data():
    """
    Doesn't differ from API at build
    """
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )
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
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )
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
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )
    node_group._envVars = {"ID": "evil"}
    with pytest.raises(JelasticObjectException):
        node_group.save()


def test_JelasticNodeGroup_envVars_raises_if_set_empty():
    """
    Saving a faked envVars without fetch will raise
    """
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )
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
        node_group = JelasticNodeGroup(
            parent=jelenv_local, node_group_from_env=get_standard_node_group()
        )
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
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )

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
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )
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
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )
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
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )
    assert not node_group.differs_from_api()
    node_group.redeploy(docker_tag="latest")


def test_JelasticNodeGroup_read_file():
    """
    We can gather a single file in a nodegroup
    """
    node_group = JelasticNodeGroup(
        parent=jelenv, node_group_from_env=get_standard_node_group()
    )
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
