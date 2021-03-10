import jelapi
from jelapi.connector import JelasticAPIConnector


def test_jelapi_api_connector_is_instance():
    assert isinstance(jelapi.api_connector(), JelasticAPIConnector)


def test_jelapi_api_connector_has_an_httpx_client():
    assert jelapi.api_connector().client


def test_jelapi_api_connector_got_api_url():
    jelapi.api_url = "https://example.com/1.0/"
    assert jelapi.api_connector().apiurl == "https://example.com/1.0/"


def test_jelapi_api_connector_got_token():
    jelapi.api_token = "secret"
    assert jelapi.api_connector().apidata["session"] == "secret"


def test_jelapi_api_connector_changes_on_api_url_change():
    jelapi.api_token = "secret"
    assert jelapi.api_connector().apidata["session"] == "secret"
