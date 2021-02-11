from enum import Enum
from json import dumps as jsondumps

from .jelasticobject import _JelasticObject
from ..exceptions import JelasticObjectException


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

    def __init__(self, *, env_from_GetEnvInfo, envGroups) -> None:
        """
        Construct a JelasticEnvironment from various data sources
        """
        self._update_from_getEnvInfo(env_from_GetEnvInfo, envGroups)

    def refresh_from_api(self) -> None:
        response = self.api._("Environment.Control.GetEnvInfo", envName=self.envName)
        self._update_from_getEnvInfo(response["env"], response["envGroups"])

    def __str__(self) -> str:
        return f"JelasticEnvironment '{self.envName}' <https://{self.domain}>"

    def _save_displayName(self):
        """
        Propagate the displayName change to the Jelastic API
        """
        if self.displayName != self._from_api["displayName"]:
            self.api._(
                "Environment.Control.SetEnvDisplayName",
                envName=self.envName,
                displayName=self.displayName,
            )
            self._from_api["displayName"] = self.displayName

    def _save_envGroups(self):
        """
        Propagate the envGroups change to the Jelastic API
        """
        if self.envGroups != self._from_api["envGroups"]:
            self.api._(
                "Environment.Control.SetEnvGroup",
                envName=self.envName,
                envGroups=jsondumps(self.envGroups),
            )
            self._from_api["envGroups"] = self.envGroups

    def _set_running_status(self):
        """
        Put Environment in the right status
        """
        if self.status != self._from_api["status"]:
            if self.status == self.Status.RUNNING:
                # TODO limit the statuses from which this is possible
                self.api._(
                    "Environment.Control.StartEnv",
                    envName=self.envName,
                )
                self._from_api["status"] = self.Status.RUNNING
            elif self.status == self.Status.STOPPED:
                if self._from_api["status"] not in [self.Status.RUNNING]:
                    raise JelasticObjectException(
                        "Cannot stop an environment not running"
                    )
                self.api._(
                    "Environment.Control.StopEnv",
                    envName=self.envName,
                )
                self._from_api["status"] = self.Status.STOPPED
            elif self.status == self.Status.SLEEPING:
                self.api._(
                    "Environment.Control.SleepEnv",
                    envName=self.envName,
                )
                self._from_api["status"] = self.Status.SLEEPING
            else:
                raise JelasticObjectException(
                    f"{self.__class__.__name__}: {self.status} not supported"
                )

    def save_to_jelastic(self):
        """
        Mandatory _JelasticObject method, to save status to Jelastic
        """
        self._save_displayName()
        self._save_envGroups()
        self._set_running_status()

    # Convenience methods

    def start(self) -> None:
        """
        Start Environment immediately
        """
        self.status = self.Status.RUNNING
        self._set_running_status()

    def stop(self) -> None:
        """
        Stop Environment immediately
        """
        self.status = self.Status.STOPPED
        self._set_running_status()

    def sleep(self) -> None:
        """
        Put Environment to sleep immediately
        """
        self.status = self.Status.SLEEPING
        self._set_running_status()