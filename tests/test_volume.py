import warnings

from jelapi.classes._volume import _JelasticVolume
from jelapi.factories import JelasticEnvironmentFactory

env = JelasticEnvironmentFactory()
cp_node_group = env.nodeGroups["cp"]


def test_JelasticVolume_init():
    """
    Test we can instantiate this without node_group
    """
    _JelasticVolume()


def test_JelasticVolume_node_group_is_deprecated():
    """
    Test we can instantiate this, and take the str representation
    """
    with warnings.catch_warnings(record=True) as warns:
        jv = _JelasticVolume(node_group=cp_node_group)
        assert len(warns) == 1
        str(jv)
