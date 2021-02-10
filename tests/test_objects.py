from unittest.mock import Mock

import pytest

from jelapi.objects import JelasticEnvironment, _JelasticObject

APIURL = "https://api.example.org/"


def get_standard_env():
    return {
        "shortdomain": "shortdomain",
        "domain": "domain",
        "envName": "envName",
        "displayName": "initial displayName",
    }


def test_JelasticObject_is_abstract():
    """
    _JelasticObject is abstract, it can't be instantiated
    """
    with pytest.raises(TypeError):
        _JelasticObject(api_connector="")


def test_JelasticEnvironment_with_enough_data():
    """
    JelasticEnvironment can be instantiated
    """
    JelasticEnvironment(
        api_connector="", env_from_GetEnvInfo=get_standard_env(), envGroups=[]
    )


def test_JelasticEnvironment_with_missing_data():
    """
    JelasticEnvironment cannot be instantiated with partial envInfo
    """
    env_truncated = get_standard_env()
    del env_truncated["displayName"]
    with pytest.raises(KeyError):
        JelasticEnvironment(
            api_connector="", env_from_GetEnvInfo=env_truncated, envGroups=[]
        )


def test_JelasticEnvironment_cannot_set_some_ro_attributes():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(
        api_connector="", env_from_GetEnvInfo=get_standard_env(), envGroups=[]
    )
    for attr in ["shortdomain", "domain", "envName"]:
        assert getattr(jelenv, attr)
        with pytest.raises(AttributeError):
            setattr(jelenv, attr, "some arbitrary value not in the object")


def test_JelasticEnvironment_doesnt_differ_from_api_initially():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(
        api_connector="", env_from_GetEnvInfo=get_standard_env(), envGroups=[]
    )
    assert not jelenv.differs_from_api()


def test_JelasticEnvironment_str_rep():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(
        api_connector="", env_from_GetEnvInfo=get_standard_env(), envGroups=[]
    )
    assert str(jelenv) == "JelasticEnvironment 'envName' <https://domain>"


def test_JelasticEnvironment_differs_from_api_if_displayName_is_changed():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(
        api_connector="", env_from_GetEnvInfo=get_standard_env(), envGroups=[]
    )
    jelenv.displayName = "different displayName"
    assert jelenv.differs_from_api()


def test_JelasticEnvironment_displayName_change_and_save_will_talk_to_API():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    api_connector = Mock()

    jelenv = JelasticEnvironment(
        api_connector=api_connector,
        env_from_GetEnvInfo=get_standard_env(),
        envGroups=[],
    )
    jelenv.displayName = "different displayName"
    jelenv.save()
    api_connector._.assert_called_once()

    api_connector.reset_mock()

    # A second save should not call the API
    jelenv.save()
    api_connector._.assert_not_called()


def test_JelasticEnvironment_differs_from_api_if_envGroups_is_changed():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(
        api_connector="", env_from_GetEnvInfo=get_standard_env(), envGroups=["A", "B"]
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
    api_connector = Mock()

    jelenv = JelasticEnvironment(
        api_connector=api_connector,
        env_from_GetEnvInfo=get_standard_env(),
        envGroups=[
            "A",
            "B",
        ],
    )
    jelenv.envGroups.append("C")
    jelenv.save()
    api_connector._.assert_called_once()

    api_connector.reset_mock()

    # A second save should not call the API
    jelenv.save()
    api_connector._.assert_not_called()
