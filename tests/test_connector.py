import pytest
import respx
from httpx import Response

from jelapi import JelasticAPIException
from jelapi.connector import JelasticAPIConnector

APIURL = "https://api.example.org/"


@respx.mock
def test_connector_successfull_empty_answer():
    """
    Check that a simple call with a 'result': 0 is successful
    """
    japic = JelasticAPIConnector(apiurl=APIURL, apitoken="string")

    getenvs_route = respx.post(f"{APIURL}environment/control/rest/getenvs").mock(
        return_value=Response(status_code=200, json={"result": 0})
    )
    japic._("Environment.Control.GetEnvs")
    assert getenvs_route.called


@respx.mock
def test_connector_failed_empty_answer():
    """
    Check that a simple call with a 'result': 1 raises
    """
    japic = JelasticAPIConnector(apiurl=APIURL, apitoken="string")

    getenvs_route = respx.post(f"{APIURL}environment/control/rest/getenvs").mock(
        return_value=Response(status_code=200, json={"result": 1})
    )
    with pytest.raises(JelasticAPIException):
        japic._("Environment.Control.GetEnvs")
        assert getenvs_route.called
