import warnings
from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes.mountpoint import JelasticMountPoint
from jelapi.exceptions import JelasticObjectException
from jelapi.factories import JelasticEnvironmentFactory

from .utils import get_standard_mount_point

# Create default environment
jelenv = JelasticEnvironmentFactory()
cp_node_group = jelenv.nodeGroups["cp"]
storage_node_group = jelenv.nodeGroups["storage"]


def test_JelasticMountPoint_simple():
    """
    Test we cannot instantiate in various situations
    """
    JelasticMountPoint()


def test_JelasticMountPoint_deprecations():
    """
    Test we cannot instantiate in various situations
    """

    with warnings.catch_warnings(record=True) as warns:
        JelasticMountPoint(node_group=cp_node_group)
        assert len(warns) == 1

    with warnings.catch_warnings(record=True) as warns:
        JelasticMountPoint(
            node_group=cp_node_group,
            mount_point_from_api=get_standard_mount_point(
                storage_node_group.nodes[0].id
            ),
        )
        assert len(warns) == 2

    # In "deprecated mode", both are needed
    with pytest.raises(TypeError):
        JelasticMountPoint(mount_point_from_api=get_standard_mount_point())


def test_JelasticMountPoint_init_from_api():
    """
    Test we can instantiate this, and take the str representation
    """
    # The Environment needs to have the target mount point ID as node
    jmp = JelasticMountPoint()
    with pytest.raises(JelasticObjectException):
        # Cannot update_from_env before attaching to node_group
        jmp.update_from_env_dict(
            get_standard_mount_point(source_node_id=storage_node_group.nodes[0].id)
        )
    jmp.attach_to_node_group(cp_node_group)
    jmp.update_from_env_dict(
        get_standard_mount_point(source_node_id=storage_node_group.nodes[0].id)
    )
    assert jmp.is_from_api
    assert str(jmp) != ""


def test_JelasticMountPoint_init_as_new():
    """
    Test we can instantiate this as new mountPoint
    """
    jmp = JelasticMountPoint(
        name="test name",
        path="/tmp/test1",
        sourceNode=storage_node_group.nodes[0],
        sourcePath="/tmp/destination",
    )
    jmp.attach_to_node_group(cp_node_group)
    assert not jmp.is_from_api


def test_JelasticMountPoint_init_no_source_avail():
    """
    Test we cannot instantiate if the api points to an unknown node
    """
    jmp = JelasticMountPoint()
    jmp.attach_to_node_group(cp_node_group)
    with pytest.raises(JelasticObjectException):
        jmp.update_from_env_dict(
            get_standard_mount_point(
                source_node_id=storage_node_group.nodes[0].id + 10
            ),
        )


def test_JelasticMountPoint_cannot_add_but_del_if_came_from_api():
    """
    We can't add a mount point that came from the API
    """

    jmp = JelasticMountPoint()
    jmp.attach_to_node_group(cp_node_group)
    jmp.update_from_env_dict(
        get_standard_mount_point(source_node_id=storage_node_group.nodes[0].id),
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
    jmp = JelasticMountPoint(
        name="test name",
        path="/tmp/test1",
        sourceNode=storage_node_group.nodes[0],
        sourcePath="/tmp/destination",
    )
    jmp.attach_to_node_group(cp_node_group)
    assert not jmp.is_from_api
    with pytest.raises(JelasticObjectException):
        jmp.del_from_api()

    jelapic()._ = Mock()
    jmp.add_to_api()
    jelapic()._.assert_called_once()
