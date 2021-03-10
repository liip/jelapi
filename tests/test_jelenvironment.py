from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.classes import JelasticEnvironment, JelasticNode
from jelapi.exceptions import JelasticObjectException

from .utils import get_standard_env, get_standard_node


def test_JelasticEnvironment_with_enough_data():
    """
    JelasticEnvironment can be instantiated
    """
    JelasticEnvironment(jelastic_env=get_standard_env())


def test_JelasticEnvironment_with_missing_data():
    """
    JelasticEnvironment cannot be instantiated with partial envInfo
    """
    env_truncated = get_standard_env()
    del env_truncated["domain"]
    with pytest.raises(KeyError):
        JelasticEnvironment(jelastic_env=env_truncated)


def test_JelasticEnvironment_getter_by_name():
    """
    JelasticEnvironment.get() works, and does one call to api
    """
    jelapic()._ = Mock(
        return_value={"env": get_standard_env(), "envGroups": []},
    )
    assert isinstance(JelasticEnvironment.get("envName"), JelasticEnvironment)
    jelapic()._.assert_called_once()


def test_JelasticEnvironment_list_all():
    """
    JelasticEnvironment.get() works, and does one call to api
    """
    jelapic()._ = Mock(
        return_value={
            "infos": [
                {"env": get_standard_env(), "envGroups": []},
            ]
        },
    )
    jelenvs = JelasticEnvironment.list()
    assert isinstance(jelenvs, dict)
    first_jelenvname = list(jelenvs)[0]
    assert isinstance(jelenvs[first_jelenvname], JelasticEnvironment)
    jelapic()._.assert_called_once()

    # If we gather the list again, it will not get called more, thanks to the lru_cache:
    jelapic()._.reset_mock()
    JelasticEnvironment.list()
    jelapic()._.assert_not_called()

    # Let's clear the lru_cache
    JelasticEnvironment.list.cache_clear()
    JelasticEnvironment.list()
    jelapic()._.assert_called_once()


def test_JelasticEnvironment_cannot_set_some_ro_attributes():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env())
    for attr in ["shortdomain", "domain", "envName"]:
        assert getattr(jelenv, attr)
        with pytest.raises(AttributeError):
            setattr(jelenv, attr, "some arbitrary value not in the object")


def test_JelasticEnvironment_doesnt_differ_from_api_initially():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env())
    assert not jelenv.differs_from_api()


def test_JelasticEnvironment_str_rep():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env())
    assert str(jelenv) == "JelasticEnvironment 'envName' <https://domain>"


def test_JelasticEnvironment_differs_from_api_if_displayName_is_changed():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env())
    jelenv.displayName = "different displayName"
    assert jelenv.differs_from_api()


def test_JelasticEnvironment_displayName_change_and_save_will_talk_to_API_twice():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """

    jelapic()._ = Mock(
        return_value={"env": get_standard_env(), "envGroups": []},
    )

    jelenv = JelasticEnvironment(
        jelastic_env=get_standard_env(),
        env_groups=[],
    )
    jelenv.displayName = "different displayName"
    jelenv.save()
    jelapic()._.assert_called()

    jelapic()._.reset_mock()

    # A second save should not call the API
    jelenv.save()
    jelapic()._.assert_not_called()


def test_JelasticEnvironment_differs_from_api_if_envGroups_is_changed():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env(), env_groups=["A", "B"])
    jelenv.envGroups.append("C")
    assert jelenv.differs_from_api()
    jelenv.envGroups = ["A", "B"]
    assert not jelenv.differs_from_api()
    jelenv.envGroups.remove("A")
    assert jelenv.differs_from_api()


def test_JelasticEnvironment_envGroups_change_and_save_will_talk_to_API():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelapic()._ = Mock(
        return_value={"env": get_standard_env(), "envGroups": []},
    )

    jelenv = JelasticEnvironment(
        jelastic_env=get_standard_env(),
        env_groups=[
            "A",
            "B",
        ],
    )
    jelenv.envGroups.append("C")
    jelenv.save()
    jelapic()._.assert_called()

    jelapic()._.reset_mock()

    # A second save should not call the API
    jelenv.save()
    jelapic()._.assert_not_called()


def test_JelasticEnvironment_can_only_be_stopped_from_running():
    """
    JelasticEnvironment cannot (yet) be put to certain states
    """
    jelenv = JelasticEnvironment(
        jelastic_env=get_standard_env(),
        env_groups=[],
    )
    JelStatus = JelasticEnvironment.Status
    for status in [
        JelStatus.UNKNOWN,
        JelStatus.LAUNCHING,
        JelStatus.SUSPENDED,
        JelStatus.CREATING,
        JelStatus.CLONING,
        JelStatus.UPDATING,
    ]:

        jelenv._status = jelenv._from_api["status"] = status
        with pytest.raises(JelasticObjectException):
            jelenv.stop()

    # But it works from running
    jelapic()._ = Mock()
    jelenv._from_api["status"] = JelStatus.RUNNING
    jelenv._status = jelenv._from_api["status"] = JelStatus.RUNNING
    jelenv.stop()
    jelapic()._.assert_called_once()


def test_JelasticEnvironment_unsupported_statuses():
    """
    JelasticEnvironment cannot (yet) be put to certain states
    """
    jelenv = JelasticEnvironment(
        jelastic_env=get_standard_env(),
        env_groups=[],
    )
    JelStatus = JelasticEnvironment.Status
    for status in [
        JelStatus.UNKNOWN,
        JelStatus.LAUNCHING,
        JelStatus.SUSPENDED,
        JelStatus.CREATING,
        JelStatus.CLONING,
        JelStatus.UPDATING,
    ]:
        jelenv.status = status
        with pytest.raises(JelasticObjectException):
            jelenv.save()


def test_JelasticEnvironment_stop_via_status():
    """
    JelasticEnvironment can be started if started, by setting the status to STOPPED, and saving
    """
    jelapic()._ = Mock(
        return_value={
            "env": get_standard_env(
                status=JelasticEnvironment.Status.STOPPED.value
            ),  # After the stop, the API returns that it was stopped
            "envGroups": [],
        }
    )

    jelenv = JelasticEnvironment(
        jelastic_env=get_standard_env(),
        env_groups=[],
    )
    jelenv.status = JelasticEnvironment.Status.STOPPED
    jelenv.save()
    assert jelenv.status == JelasticEnvironment.Status.STOPPED
    jelapic()._.assert_called()

    # A second save should not call the API
    jelapic()._.reset_mock()
    jelenv.save()
    jelapic()._.assert_not_called()


def test_JelasticEnvironment_stop_via_method():
    """
    JelasticEnvironment can be stopped if running by running the stop() method
    """
    jelapic()._ = Mock(
        return_value={
            "env": get_standard_env(
                status=JelasticEnvironment.Status.STOPPED.value
            ),  # After the stop, the API returns that it was stopped
            "envGroups": [],
        }
    )

    jelenv = JelasticEnvironment(
        jelastic_env=get_standard_env(),
        env_groups=[],
    )
    jelenv.stop()
    assert jelenv.status == JelasticEnvironment.Status.STOPPED
    jelapic()._.assert_called()

    # A second save should not call the API
    jelapic()._.reset_mock()
    jelenv.save()
    jelapic()._.assert_not_called()


def test_JelasticEnvironment_start_via_status():
    """
    JelasticEnvironment can be started if stopped or sleeping, by setting the status to RUNNING, and saving
    """
    jelapic()._ = Mock(
        return_value={
            "env": get_standard_env(
                status=JelasticEnvironment.Status.RUNNING.value
            ),  # After the stop, the API returns that it was stopped
            "envGroups": [],
        }
    )

    # Test these two starting statuses
    for status in [
        JelasticEnvironment.Status.STOPPED,
        JelasticEnvironment.Status.SLEEPING,
    ]:
        jelapic()._.reset_mock()
        jelenv = JelasticEnvironment(
            jelastic_env=get_standard_env(status.value),
            env_groups=[],
        )
        jelenv.status = JelasticEnvironment.Status.RUNNING
        jelenv.save()
        assert jelenv.status == JelasticEnvironment.Status.RUNNING
        jelapic()._.assert_called()

        # A second save should not call the API
        jelapic()._.reset_mock()
        jelenv.save()
        jelapic()._.assert_not_called()


def test_JelasticEnvironment_start_via_method():
    """
    JelasticEnvironment can be started if stopped or sleeping, with the start() method
    """
    jelapic()._ = Mock(
        return_value={
            "env": get_standard_env(
                status=JelasticEnvironment.Status.RUNNING.value
            ),  # After the stop, the API returns that it was stopped
            "envGroups": [],
        }
    )

    # Test these two starting statuses
    for status in [
        JelasticEnvironment.Status.STOPPED,
        JelasticEnvironment.Status.SLEEPING,
    ]:
        jelapic()._.reset_mock()
        jelenv = JelasticEnvironment(
            jelastic_env=get_standard_env(status.value),
            env_groups=[],
        )
        jelenv.start()
        assert jelenv.status == JelasticEnvironment.Status.RUNNING
        jelapic()._.assert_called()

        # A second save should not call the API
        jelapic()._.reset_mock()
        jelenv.save()
        jelapic()._.assert_not_called()


def test_JelasticEnvironment_sleep_via_status():
    """
    JelasticEnvironment can be put to sleep if running, by setting the status to SLEEPING, and saving
    """
    jelapic()._ = Mock(
        return_value={
            "env": get_standard_env(
                status=JelasticEnvironment.Status.SLEEPING.value
            ),  # After the sleep, the API returns that it was sleeping
            "envGroups": [],
        }
    )

    # Test these two starting statuses
    for status in [
        JelasticEnvironment.Status.STOPPED,
        JelasticEnvironment.Status.SLEEPING,
    ]:
        jelapic()._.reset_mock()
        jelenv = JelasticEnvironment(
            jelastic_env=get_standard_env(status.value),
            env_groups=[],
        )
        jelenv.status = JelasticEnvironment.Status.RUNNING
        jelenv.save()
        assert jelenv.status == JelasticEnvironment.Status.SLEEPING
        jelapic()._.assert_called()

        # A second save should not call the API
        jelapic()._.reset_mock()
        jelenv.save()
        jelapic()._.assert_not_called()


def test_JelasticEnvironment_sleep_via_method():
    """
    JelasticEnvironment can be started if stopped or sleeping, with the start() method
    """
    jelapic()._ = Mock(
        return_value={
            "env": get_standard_env(
                status=JelasticEnvironment.Status.SLEEPING.value
            ),  # After the stop, the API returns that it was stopped
            "envGroups": [],
        }
    )

    jelenv = JelasticEnvironment(
        jelastic_env=get_standard_env(JelasticEnvironment.Status.RUNNING),
        env_groups=[],
    )
    jelenv.sleep()
    assert jelenv.status == JelasticEnvironment.Status.SLEEPING
    jelapic()._.assert_called()

    # A second save should not call the API
    jelapic()._.reset_mock()
    jelenv.save()
    jelapic()._.assert_not_called()


def test_JelasticEnvironment_differs_from_api_if_extdomains_is_changed():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env())
    assert not jelenv.differs_from_api()
    jelenv.extdomains.append("test.example.com")
    assert jelenv.differs_from_api()
    jelenv.extdomains.append("test.example.org")
    assert jelenv.differs_from_api()


def test_JelasticEnvironment_extomains_change_and_save_will_talk_to_API():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    twodomains = ["test.example.com", "test.example.org"]
    jelapic()._ = Mock(
        return_value={"env": get_standard_env(extdomains=twodomains), "envGroups": []},
    )

    jelenv = JelasticEnvironment(
        jelastic_env=get_standard_env(),
        env_groups=[],
    )
    jelenv.extdomains = twodomains
    jelenv.save()
    jelapic()._.assert_called()

    jelapic()._.reset_mock()

    #  Removing a domain also calls
    jelenv.extdomains.remove("test.example.com")
    jelenv.save()
    jelapic()._.assert_called()

    jelapic()._.reset_mock()

    # A second save should not call the API
    jelenv.save()
    jelapic()._.assert_not_called()


def test_JelasticEnvironment_nodes():
    """
    JelasticEnvironment can be instantiated with nodes
    """
    nodes = []
    for i in range(3):
        node = get_standard_node()
        node["id"] = i
        nodes.append(node)

    jelenv = JelasticEnvironment(jelastic_env=get_standard_env(), nodes=nodes)
    assert not jelenv.differs_from_api()
    jelenv.nodes[0].fixedCloudlets = 8
    assert jelenv.differs_from_api()

    jelapic()._ = Mock(
        return_value={"env": get_standard_env(), "envGroups": []},
    )
    jelenv.save()
    assert not jelenv.differs_from_api()


def test_JelasticEnvironment_node_fetcher():
    """
    Test the convennience node fetcher
    """
    nodes = []
    for i in range(2):
        node = get_standard_node()
        node["id"] = i
        nodes.append(node)

    nodes[0]["nodeGroup"] = "cp"
    nodes[1]["nodeGroup"] = "sqldb"

    jelenv = JelasticEnvironment(jelastic_env=get_standard_env(), nodes=nodes)

    # Do not look by full NodeGroup object
    with pytest.raises(JelasticObjectException):
        jelenv.node_by_node_group(JelasticNode.NodeGroup.CACHE)

    # If the node's not around, exception
    with pytest.raises(JelasticObjectException):
        jelenv.node_by_node_group("nosqldb")

    assert isinstance(jelenv.node_by_node_group("cp"), JelasticNode)
