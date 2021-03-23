from copy import deepcopy
from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes import JelasticEnvironment, JelasticNode, JelasticNodeGroup
from jelapi.exceptions import JelasticObjectException

from .utils import get_standard_env, get_standard_node, get_standard_node_group

jelenv = JelasticEnvironment(jelastic_env=get_standard_env())
node_group = JelasticNodeGroup(
    parent=jelenv, node_group_from_env=get_standard_node_group()
)


def test_JelasticNode_with_enough_data():
    """
    JelasticNode can be instantiated
    """
    JelasticNode(node_group=node_group, node_from_env=get_standard_node())


def test_JelasticNode_with_missing_data():
    """
    JelasticNode can be instantiated
    """
    with pytest.raises(TypeError):
        # node_group is also mandatory
        JelasticNode(node_from_env=get_standard_node())
    with pytest.raises(TypeError):
        # node_from_env is also mandatory
        JelasticNode(node_group=node_group)

    for musthavekey in ["id", "fixedCloudlets", "flexibleCloudlets"]:
        node = get_standard_node()
        del node[musthavekey]
        with pytest.raises(KeyError):
            # missing id Dies
            JelasticNode(node_group=node_group, node_from_env=node)


def test_JelasticNode_immutable_data():
    """
    Doesn't differ from API at build
    """
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())
    assert str(node) == "JelasticNode id:1"

    with pytest.raises(AttributeError):
        node.id = 4
    with pytest.raises(AttributeError):
        node.envName = "Something else"


def test_JelasticNode_birth_from_api():
    """
    Doesn't differ from API at build
    """
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())
    assert not node.differs_from_api()


def test_JelasticNode_cloudlet_changes_let_differ_from_api():
    """
    Any cloudlet change makes it differ from API
    """
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())
    node.fixedCloudlets = 2
    assert node.differs_from_api()
    node.fixedCloudlets = 1
    assert not node.differs_from_api()
    node.flexibleCloudlets = 8
    assert node.differs_from_api()


def test_JelasticNode_flexibleCloudlet_reduction_allowance_doesnt_differ_from_api():
    """
    Setting the allowed flag doesn't make the node differ from API by itself
    """
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())
    assert not node.differs_from_api()
    assert not node.allowFlexibleCloudletsReduction

    node.allowFlexibleCloudletsReduction = True
    assert not node.differs_from_api()


def test_JelasticNode_set_cloudlets():
    """
    Setting any of fixed or flexible cloudlets calls the API once
    """
    jelapic()._ = Mock()
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())
    node.fixedCloudlets = 3
    node.save()
    jelapic()._.assert_called_once()


def test_JelasticNode_cannot_reduce_flexibleCloudlets():
    """
    Reducing the flexible cloudlets cannot be done without setting the allowed flag
    """
    node = JelasticNode(
        node_group=node_group,
        node_from_env=get_standard_node(flexible_cloudlets=8),
    )
    node.flexibleCloudlets = 7
    with pytest.raises(JelasticObjectException):
        node.save()

    jelapic()._ = Mock()
    node.allowFlexibleCloudletsReduction = True
    node.save()
    jelapic()._.assert_called_once()


def test_JelasticNode_envVars_refreshes_from_API():
    """
    Getting the envVars gets us an API call
    """
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())

    jelapic()._ = Mock(
        return_value={"object": {"VAR": "value"}},
    )
    assert "VAR" in node.envVars
    assert node.envVars["VAR"] == "value"
    # As we lazy-load, accessing the dict will call the API once
    jelapic()._.assert_called_once()
    assert not node.differs_from_api()


def test_JelasticNode_envVars_raises_if_set_without_fetch():
    """
    Saving a faked envVars without fetch will raise
    """
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())
    node._envVars = {"ID": "evil"}
    with pytest.raises(JelasticObjectException):
        node.save()


def test_JelasticNode_envVars_raises_if_set_empty():
    """
    Saving a faked envVars without fetch will raise
    """
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())
    jelapic()._ = Mock(
        return_value={"object": {"VAR": "value"}},
    )
    # fetch it
    node.envVars
    # empty it
    node._envVars = {}
    with pytest.raises(JelasticObjectException):
        node.save()


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
        node = JelasticNode(
            node_group=node_group_local,
            node_from_env=get_standard_node(),
        )
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


def test_JelasticNode_envVars_updates():
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())

    jelapic()._ = Mock(
        return_value={"object": {"VAR": "value"}},
    )
    assert node.envVars["VAR"] == "value"
    # As we lazy-load, accessing the dict will call the API once
    jelapic()._.assert_called_once()

    node.envVars["NEWVAR"] = "revolution"
    assert node.differs_from_api()
    jelapic()._ = Mock(return_value={"result": 0})
    # Save the addition, it will work, and call one _add_
    node.save()
    assert not node.differs_from_api()
    jelapic()._.assert_called_once()

    jelapic()._.reset_mock()
    del node.envVars["NEWVAR"]
    # Save the removal, it will work, and call one _remove_
    node.save()
    jelapic()._.assert_called_once()
    assert not node.differs_from_api()

    # Now test both addition and removal, this will do a single "set"
    node.envVars["NEWVAR"] = "new"
    del node.envVars["VAR"]
    jelapic()._.reset_mock()
    node.save()
    jelapic()._.assert_called_once()
    assert not node.differs_from_api()


def test_JelasticNode_exec_commands():
    """
    We can launch multiple commands in sequence in nodes
    """
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())

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
    node = JelasticNode(node_group=node_group, node_from_env=get_standard_node())

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
