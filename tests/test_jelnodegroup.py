from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes import JelasticEnvironment, JelasticNode, JelasticNodeGroup

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
