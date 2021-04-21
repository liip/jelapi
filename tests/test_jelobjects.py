from datetime import datetime

import pytest

from jelapi.classes.jelasticobject import (
    _JelasticAttribute,
    _JelasticObject,
    _JelAttrBool,
    _JelAttrDatetime,
    _JelAttrDict,
    _JelAttrInt,
    _JelAttrIPv4,
    _JelAttrList,
    _JelAttrStr,
)


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


def test_JelAttrBool_supports_bool_typecheck():
    """
    _JelAttrBool to store bools
    """

    class Test:
        jela = _JelAttrBool()

    t = Test()
    t.jela = False
    t.jela = True
    with pytest.raises(TypeError):
        t.jela = 2
    with pytest.raises(TypeError):
        t.jela = "string"


def test_JelAttrDatetime_supports_datetime_typecheck():
    """
    _JelAttrDatetimes to store datetimes
    """

    class Test:
        jela = _JelAttrDatetime()

    t = Test()
    t.jela = datetime.now()
    with pytest.raises(TypeError):
        t.jela = 2
    with pytest.raises(TypeError):
        t.jela = "string"
    with pytest.raises(TypeError):
        t.jela = False


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


def test_JelAttrIPv4_supports_ip_typecheck():
    """
    _JelAttrStr to store strings
    """

    class Test:
        ip = _JelAttrIPv4()

    t = Test()
    t.ip = "192.0.2.1"
    with pytest.raises(TypeError):
        # Too long
        t.ip = "192.0.2.1.2"
    with pytest.raises(TypeError):
        # Too short
        t.ip = "192.0.2"
    with pytest.raises(TypeError):
        # Out-of-range
        t.ip = "-1.0.2.1"
    with pytest.raises(TypeError):
        # Out-of-range
        t.ip = "256.0.2.1"
    with pytest.raises(TypeError):
        # NaN
        t.ip = "A.0.2.1"


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


def test_JelAttrList_supports_list_typecheck():
    """
    _JelAttrList to store arbitrary lists
    """

    class Test:
        jela = _JelAttrList()

    t = Test()
    t.jela = ["2", "3"]
    t.jela.append("string")
    with pytest.raises(TypeError):
        t.jela = "2"
    with pytest.raises(TypeError):
        t.jela = 2


def test_JelAttrDict_supports_dict_typecheck():
    """
    _JelAttrDict to store arbitrary dicts
    """

    class Test:
        jela = _JelAttrDict()

    t = Test()
    t.jela = {"2": 3, "3": "text"}
    t.jela["1"] = "1"
    with pytest.raises(TypeError):
        t.jela = "2"
    with pytest.raises(TypeError):
        t.jela = 2


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
