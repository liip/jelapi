import pytest

from jelapi import JelasticAPI

def test_load_class():
    japic = JelasticAPI(apiurl='https://api.example.com', apitoken='string')
    assert True
