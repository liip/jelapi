from .connector import JelasticAPIConnector
from .objects import JelasticEnvironment


class JelasticAPI:
    def __init__(self, apiurl: str, apitoken: str) -> None:
        """
        Get all needed data to connect to a Jelastic API
        """
        self._connector = JelasticAPIConnector(apiurl=apiurl, apitoken=apitoken)

    def getEnvironment(self, envName: str) -> JelasticEnvironment:
        return JelasticEnvironment(
            api_connector=self._connector,
            from_GetEnvInfo=self._connector._(
                "Environment.Control.GetEnvInfo", envName=envName
            ),
        )
