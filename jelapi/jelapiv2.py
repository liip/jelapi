from .connector import JelasticAPIConnector
from .objects import JelasticEnvironment


class JelasticAPI:
    def __init__(self, apiurl: str, apitoken: str) -> None:
        """
        Get all needed data to connect to a Jelastic API
        """
        self._connector = JelasticAPIConnector(apiurl=apiurl, apitoken=apitoken)

    def getEnvironment(self, envName: str) -> JelasticEnvironment:
        """
        Get environment by envName
        """
        # The connector will fail if response is not 0
        response = self._connector._("Environment.Control.GetEnvInfo", envName=envName)

        return JelasticEnvironment(
            api_connector=self._connector,
            env_from_GetEnvInfo=response["env"],
        )
