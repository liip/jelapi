from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes import JelasticNode


def get_standard_node():
    return {
        "id": 1,
        "fixedCloudlets": 1,
        "flexibleCloudlets": 1,
        "intIP": "192.0.2.1",
        "nodeGroup": "cp",
    }


def test_JelasticNode_with_enough_data():
    """
    JelasticNode can be instantiated
    """
    JelasticNode(envName="", node_from_env=get_standard_node())


def test_JelasticNode_with_missing_data():
    """
    JelasticNode can be instantiated
    """
    with pytest.raises(TypeError):
        # envName is mandatory
        JelasticNode(node_from_env=get_standard_node())
    with pytest.raises(TypeError):
        # node_from_env is also mandatory
        JelasticNode(envName="name")

    for musthavekey in ["id", "fixedCloudlets", "flexibleCloudlets"]:
        node = get_standard_node()
        del node[musthavekey]
        with pytest.raises(KeyError):
            # missing id Dies
            JelasticNode(envName="", node_from_env=node)


def test_JelasticNode_immutable_data():
    """
    Doesn't differ from API at build
    """
    node = JelasticNode(envName="", node_from_env=get_standard_node())
    assert str(node) == "JelasticNode id:1"

    with pytest.raises(AttributeError):
        node.id = 4
    with pytest.raises(AttributeError):
        node.envName = "Something else"


def test_JelasticNode_birth_from_api():
    """
    Doesn't differ from API at build
    """
    node = JelasticNode(envName="", node_from_env=get_standard_node())
    assert not node.differs_from_api()


def test_JelasticNode_cloudlet_changes_let_differ_from_api():
    """
    Any cloudlet change makes it differ from API
    """
    node = JelasticNode(envName="", node_from_env=get_standard_node())
    node.fixedCloudlets = 2
    assert node.differs_from_api()
    node.fixedCloudlets = 1
    assert not node.differs_from_api()
    node.flexibleCloudlets = 8
    assert node.differs_from_api()


def test_JelasticNode_set_cloudlets():
    """
    Setting any of fixed or flexible cloudlets calls the API once
    """
    jelapic()._ = Mock()
    node = JelasticNode(envName="", node_from_env=get_standard_node())
    node.fixedCloudlets = 3
    node.save()
    jelapic()._.assert_called_once()
