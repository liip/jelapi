from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic
from jelapi.exceptions import JelasticObjectException
from jelapi.classes import JelasticEnvironment
from jelapi.classes.jelasticobject import (
    _JelasticObject,
    _JelasticAttribute,
    _JelAttrStr,
    _JelAttrInt,
)


def get_standard_env(status=JelasticEnvironment.Status.RUNNING.value):
    return {
        "shortdomain": "shortdomain",
        "domain": "domain",
        "envName": "envName",
        "displayName": "initial displayName",
        "status": status,
    }


def test_JelasticAttribute_is_permissive_by_default():
    """
    _JelasticAttribute is a descriptor class
    """

    class Test:
        jela = _JelasticAttribute()

    t = Test()
    t.jela = "another string"
    t.jela = 2
    t.jela = [2, "string"]


def test_JelAttrStr_supports_str_typecheck():
    """
    _JelAttrStr to store strings
    """

    class Test:
        jela = _JelAttrStr()

    t = Test()
    t.jela = "a string"
    t.jela = "another string"
    with pytest.raises(TypeError):
        t.jela = 2
    with pytest.raises(TypeError):
        t.jela = [2, "string"]


def test_JelAttrInt_supports_int_typecheck():
    """
    _JelAttrInt to store ints
    """

    class Test:
        jela = _JelAttrInt()

    t = Test()
    t.jela = 3
    t.jela = 5
    with pytest.raises(TypeError):
        t.jela = "2"
    with pytest.raises(TypeError):
        t.jela = [2, "string"]


def test_JelasticAttribute_can_be_read_only():
    """
    _JelasticAttribute is a descriptor
    """

    class Test:
        jela = _JelasticAttribute(read_only=True)

    t = Test()
    # To set in nevertheless, set the private counterpart.
    t._jela = "a string"
    assert t.jela == "a string"
    with pytest.raises(AttributeError):
        t.jela = "another string"


def test_JelasticObject_is_abstract():
    """
    _JelasticObject is abstract, it can't be instantiated
    """
    with pytest.raises(TypeError):
        _JelasticObject()


def test_JelasticEnvironment_with_enough_data():
    """
    JelasticEnvironment can be instantiated
    """
    JelasticEnvironment(jelastic_env=get_standard_env(), env_groups=[])


def test_JelasticEnvironment_with_missing_data():
    """
    JelasticEnvironment cannot be instantiated with partial envInfo
    """
    env_truncated = get_standard_env()
    del env_truncated["displayName"]
    with pytest.raises(KeyError):
        JelasticEnvironment(jelastic_env=env_truncated, env_groups=[])


def test_JelasticEnvironment_getter_by_name():
    """
    JelasticEnvironment.get() works, and does one call to api
    """
    jelapic()._ = Mock(
        return_value={"env": get_standard_env(), "envGroups": []},
    )
    assert isinstance(JelasticEnvironment.get("envName"), JelasticEnvironment)
    jelapic()._.assert_called_once()


def test_JelasticEnvironment_cannot_set_some_ro_attributes():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env(), env_groups=[])
    for attr in ["shortdomain", "domain", "envName"]:
        assert getattr(jelenv, attr)
        with pytest.raises(AttributeError):
            setattr(jelenv, attr, "some arbitrary value not in the object")


def test_JelasticEnvironment_doesnt_differ_from_api_initially():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env(), env_groups=[])
    assert not jelenv.differs_from_api()


def test_JelasticEnvironment_str_rep():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env(), env_groups=[])
    assert str(jelenv) == "JelasticEnvironment 'envName' <https://domain>"


def test_JelasticEnvironment_differs_from_api_if_displayName_is_changed():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(jelastic_env=get_standard_env(), env_groups=[])
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
