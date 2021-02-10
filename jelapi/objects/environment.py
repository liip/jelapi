from enum import Enum
from json import dumps as jsondumps

from .jelasticobject import _JelasticObject


class JelasticEnvironment(_JelasticObject):
    """
    Represents a Jelastic Environment
    """

    _jelattributes = [
        "displayName",
        "envGroups",
        "status",
    ]
    _readonly_jelattributes = [
        "envName",
        "shortdomain",
        "domain",
    ]

    class Status(Enum):
        """
        Standard statuses
        Latest reference https://github.com/jelastic/localizations/blob/master/English/5.4/%5Blang-en.js%5D#L999
        """

        UNKNOWN = 0
        RUNNING = 1
        STOPPED = 2
        LAUNCHING = 3
        SLEEPING = 4
        SUSPENDED = 5
        CREATING = 6
        CLONING = 7
        UPDATING = 12

    def _update_from_getEnvInfo(self, env_from_GetEnvInfo, envGroups) -> None:
        """
        Construct/Update our object from the structure
        """
        if env_from_GetEnvInfo:
            # Allow exploration of the returned object, but don't act on it.
            self._env = env_from_GetEnvInfo
            # Read-only attributes
            self._shortdomain = self._env["shortdomain"]
            self._envName = self._env["envName"]
            self._domain = self._env["domain"]

            # Read-write attributes
            self.displayName = self._env["displayName"]
            self.status = next(
                (
                    status
                    for status in self.Status
                    if status.value == self._env["status"]
                ),
                self.Status.UNKNOWN,
            )

        self.envGroups = envGroups

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __init__(self, *, api_connector, env_from_GetEnvInfo, envGroups) -> None:
        """
        Construct a JelasticEnvironment from various data sources
        """
        super().__init__(api_connector=api_connector)

        self._update_from_getEnvInfo(env_from_GetEnvInfo, envGroups)

    def refresh_from_api(self) -> None:
        response = self._api_connector._(
            "Environment.Control.GetEnvInfo", envName=self.envName
        )
        self._update_from_getEnvInfo(response["env"], response["envGroups"])

    def __str__(self) -> str:
        return f"JelasticEnvironment '{self.envName}' <https://{self.domain}>"

    def _save_displayName(self):
        """
        Propagate the displayName change to the Jelastic API
        """
        if self.displayName != self._from_api["displayName"]:
            self._api_connector._(
                "Environment.Control.SetEnvDisplayName",
                envName=self.envName,
                displayName=self.displayName,
            )

    def _save_envGroups(self):
        """
        Propagate the envGroups change to the Jelastic API
        """
        if self.envGroups != self._from_api["envGroups"]:
            self._api_connector._(
                "Environment.Control.SetEnvGroup",
                envName=self.envName,
                envGroups=jsondumps(self.envGroups),
            )

    def save_to_jelastic(self):
        self._save_displayName()
        self._save_envGroups()
