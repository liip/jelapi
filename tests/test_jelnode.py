import warnings
from copy import deepcopy
from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes import JelasticNode
from jelapi.exceptions import JelasticObjectException
from jelapi.factories import (
    JelasticEnvironmentFactory,
    JelasticNodeFactory,
)

from .utils import get_standard_node

jelenv = JelasticEnvironmentFactory()
node_group = list(jelenv.nodeGroups.values())[0]


def test_JelasticNode_simple_load():
    """
    JelasticNode can be instantiated as-is
    """
    JelasticNode()


def test_JelasticNode_with_node_group():
    """
    JelasticNode can be instantiated with just node_group
    """
    with warnings.catch_warnings(record=True) as warns:
        JelasticNode(node_group=node_group)
        # There was one deprecationWarning for node_from_env() usage
        assert len(warns) == 1
        assert issubclass(warns[0].category, DeprecationWarning)


def test_JelasticNode_with_node_from_env():
    """
    JelasticNode can be instantiated with just node_from_env
    """
    with warnings.catch_warnings(record=True) as warns:
        JelasticNode(node_from_env=get_standard_node())
        # There was one deprecationWarning for node_from_env() usage
        assert len(warns) == 1
        assert issubclass(warns[0].category, DeprecationWarning)


def test_JelasticNode_update_from_env_dict():
    """
    JelasticNode can get an env dict
    """
    node = JelasticNode()
    assert not node.is_from_api
    node.update_from_env_dict(node_from_env=get_standard_node())
    assert node.is_from_api


def test_JelasticNode_update_from_broken_env_dict():
    """
    JelasticNode cannot be updated from env with missing items
    """
    for musthavekey in [
        "id",
        "name",
        "nodemission",
        "status",
        "type",
        "fixedCloudlets",
        "flexibleCloudlets",
    ]:
        node = get_standard_node()
        del node[musthavekey]

        n = JelasticNode()
        with pytest.raises(KeyError):
            # missing items raises
            n.update_from_env_dict(node)


def test_JelasticNode_update_from_dict_with_unknown_nodeType():
    """
    JelasticNode cannot be instantiated with weird nodeTypes
    """
    node = get_standard_node()
    node["nodeType"] = "this-is-unknown-type"

    n = JelasticNode()
    with pytest.raises(JelasticObjectException):
        n.update_from_env_dict(node)


def test_JelasticNode_factory():
    node = JelasticNodeFactory()
    assert node.is_from_api

    with pytest.raises(JelasticObjectException):
        # envVars cannot be fetched if not from API
        node.envVars


def test_JelasticNode_immutable_data():
    """
    Doesn't differ from API at build
    """
    node = JelasticNodeFactory()
    node._id = 3
    assert str(node) == "JelasticNode id:3"

    with pytest.raises(AttributeError):
        node.id = 4
    with pytest.raises(AttributeError):
        node.envName = "Something else"


def test_JelasticNode_birth_from_api():
    """
    Doesn't differ from API at build
    """
    node = JelasticNodeFactory()
    assert not node.differs_from_api()


def test_JelasticNode_cloudlet_changes_let_differ_from_api():
    """
    Any cloudlet change makes it differ from API
    """
    node = JelasticNodeFactory()
    # Force 1 as coming from API
    node._from_api["fixedCloudlets"] = 1
    node.fixedCloudlets = 8
    assert node.differs_from_api()
    node.fixedCloudlets = 1
    assert not node.differs_from_api()
    node.flexibleCloudlets = 8
    assert node.differs_from_api()


def test_JelasticNode_flexibleCloudlet_reduction_allowance_doesnt_differ_from_api():
    """
    Setting the allowed flag doesn't make the node differ from API by itself
    """
    node = JelasticNodeFactory()
    assert not node.differs_from_api()
    assert not node.allowFlexibleCloudletsReduction

    node.allowFlexibleCloudletsReduction = True
    assert not node.differs_from_api()


def test_JelasticNode_cannot_be_api_updated_without_node_group():
    """
    Test that without envName, no API updates can happen
    """
    node = JelasticNode()
    with pytest.raises(JelasticObjectException):
        node.raise_unless_can_update_to_api()

    # Setting the node_group fixes that
    node.attach_to_node_group(node_group=node_group)
    node.raise_unless_can_update_to_api()


def test_JelasticNode_set_cloudlets():
    """
    Setting any of fixed or flexible cloudlets calls the API once
    """
    jelapic()._ = Mock()
    node = JelasticNodeFactory()
    node.attach_to_node_group(node_group)
    node.fixedCloudlets = 3
    node.save()
    jelapic()._.assert_called_once()


def test_JelasticNode_cannot_reduce_flexibleCloudlets():
    """
    Reducing the flexible cloudlets cannot be done without setting the allowed flag
    """
    node = JelasticNodeFactory()
    node.attach_to_node_group(node_group)
    # 8 came from API
    node._from_api["flexibleCloudlets"] = 8

    node.flexibleCloudlets = 7
    with pytest.raises(JelasticObjectException):
        node.save()

    jelapic()._ = Mock()
    node.allowFlexibleCloudletsReduction = True
    node.save()
    jelapic()._.assert_called_once()


def test_JelasticNode_envVars_works_but_takes_from_node_group():
    """
    Getting the envVars gets us the nodeGroups'
    """
    node_group._envVars = {"TEST": "example.com"}
    node_group._envVars_need_fetching = False

    node = JelasticNodeFactory()
    node.attach_to_node_group(node_group)

    assert "TEST" in node.envVars
    assert node.envVars["TEST"] == "example.com"


def test_JelasticNode_envVars_raises_if_env_is_not_running():
    """
    Saving a faked envVars without fetch will raise
    """
    from jelapi.classes import JelasticEnvironment

    JelStatus = JelasticEnvironment.Status
    for status in JelStatus:
        jelenv_local = deepcopy(jelenv)
        jelenv_local.status = status
        node_group_local = deepcopy(node_group)
        node_group_local._parent = jelenv_local

        node = JelasticNodeFactory()
        node.attach_to_node_group(node_group_local)

        jelapic()._ = Mock(
            return_value={"object": {"VAR": "value"}},
        )
        if status in [
            JelStatus.RUNNING,
            JelStatus.CREATING,
            JelStatus.CLONING,
        ]:
            node.envVars
        else:
            with pytest.raises(JelasticObjectException):
                node.envVars


def test_JelasticNode_links_empty():
    """
    Getting the links works
    """
    node = JelasticNodeFactory()
    assert node.links == []


def test_JelasticNode_links_only_from_inwards():
    """
    Getting the links works
    """
    node = JelasticNode()
    ndict = get_standard_node()
    ndict["customitem"] = {
        "dockerLinks": [
            {"type": "IN", "sourceNodeId": 0},
            {"type": "OUT", "sourceNodeId": 10},
        ]
    }
    node.update_from_env_dict(ndict)
    assert len(node.links) == 1
    assert node.links[0]["sourceNodeId"] == 0


def test_JelasticNode_exec_commands():
    """
    We can launch multiple commands in sequence in nodes
    """
    node = JelasticNode()
    node.attach_to_node_group(node_group)
    node.update_from_env_dict(get_standard_node())

    jelapic()._ = Mock(
        return_value={
            "responses": [
                {
                    "errOut": "",
                    "exitStatus": 0,
                    "nodeid": node.id,
                    "out": "",
                    "result": 0,
                },
                {
                    "errOut": "",
                    "exitStatus": 0,
                    "nodeid": node.id,
                    "out": "example.com",
                    "result": 0,
                },
            ],
            "result": 0,
        },
    )
    assert node.execute_commands(["/bin/true", "echo 'example.com'"])
    jelapic()._.assert_called_once()
    with pytest.raises(TypeError):
        # We can't shortcut the list for a single command
        node.execute_commands("/bin/true")


def test_JelasticNode_exec_command():
    """
    We can launch a single command in a node
    """
    node = JelasticNodeFactory()
    node.attach_to_node_group(node_group)

    jelapic()._ = Mock(
        return_value={
            "responses": [
                {
                    "errOut": "",
                    "exitStatus": 0,
                    "nodeid": node.id,
                    "out": "",
                    "result": 0,
                }
            ],
            "result": 0,
        },
    )
    assert node.execute_command("/bin/true")
    jelapic()._.assert_called_once()
    with pytest.raises(TypeError):
        # We can't extend the single command for a list
        node.execute_command(["/bin/true", "echo 'example.com'"])


def test_JelasticNode_read_file():
    """
    We can gather a single file in a node
    """
    node = JelasticNodeFactory()
    node.attach_to_node_group(node_group)

    jelapic()._ = Mock(
        return_value={
            "body": "Text content",
            "result": 0,
        },
    )
    with pytest.raises(TypeError):
        # We can't read no file
        node.read_file("")

    body = node.read_file("/tmp/test")
    jelapic()._.assert_called_once()
    assert body == "Text content"
