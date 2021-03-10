# JelasticAPI

# Configuration variables
api_url = None
api_token = None
hoster_domain = None


from .exceptions import JelasticAPIException  # noqa
from .classes import JelasticEnvironment, JelasticNode # noqa

_api_connector = None


def api_connector():
    """
    Get the global jelapi api_connector
    """
    global _api_connector, api_url, api_token
    from .connector import JelasticAPIConnector

    if (
        isinstance(_api_connector, JelasticAPIConnector)
        and _api_connector.is_functional()
    ):
        # Only return the global one if it is somewhat functional
        return _api_connector

    _api_connector = JelasticAPIConnector(apiurl=api_url, apitoken=api_token)
    return _api_connector
