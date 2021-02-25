import pytest

from jelapi.classes.jelasticobject import (
    _JelasticObject,
    _JelasticAttribute,
    _JelAttrStr,
    _JelAttrInt,
    _JelAttrList,
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
