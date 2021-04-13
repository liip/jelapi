import pytest

from jelapi.classes._volume import _JelasticVolume
from jelapi.classes.environment import JelasticEnvironment
from jelapi.classes.nodegroup import JelasticNodeGroup
from jelapi.exceptions import JelasticObjectException

from .utils import get_standard_env, get_standard_node_group

env = JelasticEnvironment(jelastic_env=get_standard_env())
cp_node_group = JelasticNodeGroup(
    parent=env, node_group_from_env=get_standard_node_group()
)


def test_JelasticVolume_init():
    """
    Test we can instantiate this, and take the str representation
    """
    jv = _JelasticVolume(node_group=cp_node_group)
    str(jv)


def test_JelasticVolume_missing_node_group():
    """
    Test we cannot instantiate this without node_group
    """
    with pytest.raises(JelasticObjectException):
        _JelasticVolume()
