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


def test_connector_refuses_wrongly_formatted_functions():
    """
    Check that functions need to be in the First.Second.Word format
    """
    japic = JelasticAPIConnector(apiurl=APIURL, apitoken="string")

    with pytest.raises(JelasticAPIException):
        # 3 dots
        japic._("Not.A.Function.Call")

    with pytest.raises(JelasticAPIException):
        # 2 dots
        japic._("Not_A.Function_Call")

    with respx.mock() as respx_mock:
        # 3 dots is a valid function
        # TODO: Perhaps we allow-list the functions we know
        uncontrolled_route = respx_mock.post(f"{APIURL}a/function/rest/call").mock(
            return_value=Response(status_code=200, json={"result": 0})
        )
        japic._("A.Function.Call")
        assert uncontrolled_route.called
