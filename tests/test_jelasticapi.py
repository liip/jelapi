from unittest.mock import MagicMock

import respx
from httpx import Response, codes

from jelapi.connector import JelasticAPIConnector
from jelapi.jelapiv2 import JelasticAPI
from jelapi.objects import JelasticEnvironment

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
        "envGroups": [
            "envGroup1",
            "envGroup2",
        ],
    }


def test_JelasticAPI_has_connector():
    jelapi = JelasticAPI(apiurl=APIURL, apitoken="")
    assert isinstance(jelapi._connector, JelasticAPIConnector)


def test_JelasticAPI_getEnvironment_returnsJelasticEnvironment():
    jelapi = JelasticAPI(apiurl=APIURL, apitoken="")
    jelapi._connector._ = MagicMock(return_value=get_standard_envinfo())

    jelenv = jelapi.getEnvironment(envName="testenvironment")
    assert isinstance(jelenv, JelasticEnvironment)


@respx.mock
def test_JelasticAPI_getEnvironment_does_one_API_call():
    jelapi = JelasticAPI(apiurl=APIURL, apitoken="")

    getenvinfo_route = respx.post(f"{APIURL}environment/control/rest/getenvinfo").mock(
        return_value=Response(status_code=codes.OK, json=get_standard_envinfo())
    )
    jelapi.getEnvironment(envName="testenvironment")
    assert getenvinfo_route.called
