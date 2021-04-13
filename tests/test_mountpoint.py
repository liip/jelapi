from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes.environment import JelasticEnvironment
from jelapi.classes.mountpoint import JelasticMountPoint
from jelapi.classes.node import JelasticNode
from jelapi.classes.nodegroup import JelasticNodeGroup
from jelapi.exceptions import JelasticObjectException

from .utils import (
    get_standard_env,
    get_standard_mount_point,
    get_standard_node,
    get_standard_node_group,
)

# Create default environment
jelenv = JelasticEnvironment(jelastic_env=get_standard_env())

cp_node_group = JelasticNodeGroup(
    parent=jelenv, node_group_from_env=get_standard_node_group()
)
cp_node_group._nodes = [
    JelasticNode(node_group=cp_node_group, node_from_env=get_standard_node())
]
storage_node_group = JelasticNodeGroup(
    parent=jelenv, node_group_from_env=get_standard_node_group()
)
storage_node_group._nodes = [
    JelasticNode(node_group=storage_node_group, node_from_env=get_standard_node())
]
jelenv._nodeGroups = {"cp": cp_node_group, "storage": storage_node_group}


def test_JelasticMountPoint_init_from_api():
    """
    Test we can instantiate this, and take the str representation
    """
    # The Environment needs to have the target mount point ID as node
    jmp = JelasticMountPoint(
        node_group=cp_node_group,
        mount_point_from_api=get_standard_mount_point(
            source_node_id=storage_node_group.nodes[0].id
        ),
    )
    assert jmp.is_from_api
    assert str(jmp) != ""


def test_JelasticMountPoint_init_as_new():
    """
    Test we can instantiate this as new mountPoint
    """
    jmp = JelasticMountPoint(
        node_group=cp_node_group,
        name="test name",
        path="/tmp/test1",
        sourceNode=storage_node_group.nodes[0],
        sourcePath="/tmp/destination",
    )
    assert not jmp.is_from_api


def test_JelasticMountPoint_init_missing():
    """
    Test we cannot instantiate in various situations
    """
    with pytest.raises(JelasticObjectException):
        JelasticMountPoint()
    with pytest.raises(TypeError):
        JelasticMountPoint(node_group=cp_node_group)
    with pytest.raises(JelasticObjectException):
        JelasticMountPoint(
            mount_point_from_api=get_standard_mount_point(
                source_node_id=storage_node_group.nodes[0].id
            ),
        )


def test_JelasticMountPoint_init_no_source_avail():
    """
    Test we cannot instantiate if the api points to an unknown node
    """
    with pytest.raises(JelasticObjectException):
        JelasticMountPoint(
            node_group=cp_node_group,
            mount_point_from_api=get_standard_mount_point(
                source_node_id=storage_node_group.nodes[0].id + 10
            ),
        )


def test_JelasticMountPoint_cannot_add_but_del_if_came_from_api():
    """
    We can't add a mount point that came from the API
    """
    # The Environment needs to have the target mount point ID as node
    jmp = JelasticMountPoint(
        node_group=cp_node_group,
        mount_point_from_api=get_standard_mount_point(
            source_node_id=storage_node_group.nodes[0].id
        ),
    )
    assert jmp.is_from_api
    with pytest.raises(JelasticObjectException):
        jmp.add_to_api()

    jelapic()._ = Mock()
    jmp.del_from_api()
    jelapic()._.assert_called_once()


def test_JelasticMountPoint_cannot_del_but_add_if_new():
    """
    We can't add a mount point that came from the API
    """
    # The Environment needs to have the target mount point ID as node
    jmp = JelasticMountPoint(
        node_group=cp_node_group,
        name="test name",
        path="/tmp/test1",
        sourceNode=storage_node_group.nodes[0],
        sourcePath="/tmp/destination",
    )
    assert not jmp.is_from_api
    with pytest.raises(JelasticObjectException):
        jmp.del_from_api()

    jelapic()._ = Mock()
    jmp.add_to_api()
    jelapic()._.assert_called_once()
