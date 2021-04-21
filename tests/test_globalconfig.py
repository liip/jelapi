import jelapi
from jelapi.connector import JelasticAPIConnector


def test_jelapi_api_connector_is_instance():
    assert isinstance(jelapi.api_connector(), JelasticAPIConnector)


def test_jelapi_api_connector_has_an_httpx_client():
    assert jelapi.api_connector().client


def test_jelapi_api_connector_sets_api_url():
    jelapi.api_url = "https://api.example.org/2.0/"
    assert jelapi.api_connector().apiurl == "https://api.example.org/2.0/"


def test_jelapi_api_connector_got_token():
    jelapi.api_token = "new-secret"
    assert jelapi.api_connector().apidata["session"] == "new-secret"
