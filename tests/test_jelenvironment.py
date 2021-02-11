import respx
from httpx import Response, codes

from unittest.mock import Mock

import pytest

from jelapi import api_connector as jelapic

from jelapi.objects import JelasticEnvironment
from jelapi.objects.jelasticobject import _JelasticObject


def get_standard_env(status=JelasticEnvironment.Status.RUNNING.value):
    return {
        "shortdomain": "shortdomain",
        "domain": "domain",
        "envName": "envName",
        "displayName": "initial displayName",
        "status": status,
    }


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
    JelasticEnvironment(env_from_GetEnvInfo=get_standard_env(), envGroups=[])


def test_JelasticEnvironment_with_missing_data():
    """
    JelasticEnvironment cannot be instantiated with partial envInfo
    """
    env_truncated = get_standard_env()
    del env_truncated["displayName"]
    with pytest.raises(KeyError):
        JelasticEnvironment(env_from_GetEnvInfo=env_truncated, envGroups=[])


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
    jelenv = JelasticEnvironment(env_from_GetEnvInfo=get_standard_env(), envGroups=[])
    for attr in ["shortdomain", "domain", "envName"]:
        assert getattr(jelenv, attr)
        with pytest.raises(AttributeError):
            setattr(jelenv, attr, "some arbitrary value not in the object")


def test_JelasticEnvironment_doesnt_differ_from_api_initially():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(env_from_GetEnvInfo=get_standard_env(), envGroups=[])
    assert not jelenv.differs_from_api()


def test_JelasticEnvironment_str_rep():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(env_from_GetEnvInfo=get_standard_env(), envGroups=[])
    assert str(jelenv) == "JelasticEnvironment 'envName' <https://domain>"


def test_JelasticEnvironment_differs_from_api_if_displayName_is_changed():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(env_from_GetEnvInfo=get_standard_env(), envGroups=[])
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
        env_from_GetEnvInfo=get_standard_env(),
        envGroups=[],
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
    jelenv = JelasticEnvironment(
        env_from_GetEnvInfo=get_standard_env(), envGroups=["A", "B"]
    )
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
        env_from_GetEnvInfo=get_standard_env(),
        envGroups=[
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
        env_from_GetEnvInfo=get_standard_env(),
        envGroups=[],
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
        env_from_GetEnvInfo=get_standard_env(),
        envGroups=[],
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
            env_from_GetEnvInfo=get_standard_env(status.value),
            envGroups=[],
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
            env_from_GetEnvInfo=get_standard_env(status.value),
            envGroups=[],
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
            env_from_GetEnvInfo=get_standard_env(status.value),
            envGroups=[],
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
        env_from_GetEnvInfo=get_standard_env(JelasticEnvironment.Status.RUNNING),
        envGroups=[],
    )
    jelenv.sleep()
    assert jelenv.status == JelasticEnvironment.Status.SLEEPING
    jelapic()._.assert_called()

    # A second save should not call the API
    jelapic()._.reset_mock()
    jelenv.save()
    jelapic()._.assert_not_called()
