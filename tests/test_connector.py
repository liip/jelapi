import pytest
import respx
from httpx import Response, codes

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
        return_value=Response(status_code=codes.OK, json={"result": 0})
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
        return_value=Response(status_code=codes.OK, json={"result": 1})
    )
    with pytest.raises(JelasticAPIException):
        japic._("Environment.Control.GetEnvs")
        assert getenvs_route.called


@respx.mock
def test_connector_fails_on_non_OK_status():
    """
    Check that a simple call with a 'result': 0 but an HTTP status != 200 raises
    """
    japic = JelasticAPIConnector(apiurl=APIURL, apitoken="string")

    getenvs_route = respx.post(f"{APIURL}environment/control/rest/getenvs").mock(
        return_value=Response(status_code=codes.IM_A_TEAPOT, json={"result": 0})
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


def test_connector_is_not_functional_if_apidata_not_a_list():
    japic = JelasticAPIConnector(apiurl=None, apitoken=None)
    japic.apidata = "some-str"
    assert not japic.is_functional()


def test_connector_is_not_functional_if_apiurl_is_deleted():
    japic = JelasticAPIConnector(apiurl=None, apitoken=None)
    del japic.apiurl
    assert not japic.is_functional()


def test_connector_is_not_functional_without_api_url():
    japic = JelasticAPIConnector(apiurl="", apitoken="secret")
    assert not japic.is_functional()


def test_connector_is_not_functional_without_api_token():
    japic = JelasticAPIConnector(apiurl=APIURL, apitoken="")
    assert not japic.is_functional()


def test_connector_is_functional_with_both():
    japic = JelasticAPIConnector(apiurl=APIURL, apitoken="secret")
    assert japic.is_functional()
