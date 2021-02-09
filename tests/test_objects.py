import pytest

from unittest.mock import Mock

from jelapi.exceptions import JelasticObjectException
from jelapi.objects import JelasticEnvironment, _JelasticObject

APIURL = "https://api.example.org/"


def get_standard_envinfo():
    return {
        "result": 0,
        "env": {
            "shortdomain": "shortdomain",
            "domain": "domain",
            "envName": "envName",
            "displayName": "initial displayName",
        },
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
    JelasticEnvironment(api_connector="", from_GetEnvInfo=get_standard_envinfo())


def test_JelasticEnvironment_with_missing_result():
    """
    JelasticEnvironment cannot be instantiated with partial envInfo
    """
    envinfo_truncated = get_standard_envinfo()
    del envinfo_truncated["result"]
    with pytest.raises(JelasticObjectException):
        JelasticEnvironment(api_connector="", from_GetEnvInfo=envinfo_truncated)
    # It also fails with non-zero result
    envinfo_truncated["result"] = 2
    with pytest.raises(JelasticObjectException):
        JelasticEnvironment(api_connector="", from_GetEnvInfo=envinfo_truncated)


def test_JelasticEnvironment_with_missing_data():
    """
    JelasticEnvironment cannot be instantiated with partial envInfo
    """
    envinfo_truncated = get_standard_envinfo()
    del envinfo_truncated["env"]["displayName"]
    with pytest.raises(KeyError):
        JelasticEnvironment(api_connector="", from_GetEnvInfo=envinfo_truncated)


def test_JelasticEnvironment_cannot_set_some_ro_attributes():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(
        api_connector="", from_GetEnvInfo=get_standard_envinfo()
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
        api_connector="", from_GetEnvInfo=get_standard_envinfo()
    )
    assert not jelenv.differs_from_api()


def test_JelasticEnvironment_str_rep():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(
        api_connector="", from_GetEnvInfo=get_standard_envinfo()
    )
    assert str(jelenv) == "JelasticEnvironment 'envName' <https://domain>"


def test_JelasticEnvironment_differs_from_api_if_displayName_is_changed():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    jelenv = JelasticEnvironment(
        api_connector="", from_GetEnvInfo=get_standard_envinfo()
    )
    jelenv.displayName = "different displayName"
    assert jelenv.differs_from_api()


def test_JelasticEnvironment_displayName_change_and_save_will_talk_to_API():
    """
    JelasticEnvironment can be instantiated, but some read-only attributes can be read, but not written
    """
    api_connector = Mock()

    jelenv = JelasticEnvironment(
        api_connector=api_connector, from_GetEnvInfo=get_standard_envinfo()
    )
    jelenv.displayName = "different displayName"
    jelenv.save()
    api_connector._.assert_called_once()

    api_connector.reset_mock()

    # A second save should not call the API
    jelenv.save()
    api_connector._.assert_not_called()
