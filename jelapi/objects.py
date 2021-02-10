from abc import ABC, abstractmethod
from copy import deepcopy
from json import dumps as jsondumps


class _JelasticObject(ABC):
    """
    Any Jelastic Object, that keeps the last data as fetched from the API
    """

    _jelattributes = []
    _readonly_jelattributes = []
    _from_api = {}
    _api_connector = None

    def __init__(self, *, api_connector) -> None:
        self._api_connector = api_connector
        assert self._api_connector is not None

    def __getattribute__(self, name):
        """
        Override getter to let the read-only attributes be accessible directly
        """
        # Always return private attributes
        if name[0] == "_":
            return object.__getattribute__(self, name)
        # Redirect readonly attributes to their private counterparts
        if name in self._readonly_jelattributes:
            return object.__getattribute__(self, f"_{name}")
        # Fallback
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        """
        Override setter to forbid updating the attributes we cannot save in Jelastic.
        """
        if name in self._readonly_jelattributes:
            raise AttributeError(f"{self.__class__.__name__}: '{name}' is read only.")
        object.__setattr__(self, name, value)

    def copy_self_as_from_api(self) -> None:
        """
        Store a copy of ourselves, as it was from API
        """
        # Verify the attributes got copied correctly
        for jelattribute in self._jelattributes:
            self._from_api[jelattribute] = deepcopy(getattr(self, jelattribute))

    def differs_from_api(self) -> bool:
        for jelattribute in self._jelattributes:
            if getattr(self, jelattribute) != self._from_api[jelattribute]:
                return True

    @abstractmethod
    def save_to_jelastic(self) -> None:
        """
        If needed, do what's needed to save the object to the API
        DO NOT update the object. That'd done in refresh_from_api
        """

    @abstractmethod
    def refresh_from_api(self) -> None:
        """
        Refresh current object from the API
        """

    def save(self) -> bool:
        """
        Save the changes staged in attributes
        """
        if self.differs_from_api():
            # Implements the saving of the changes to Jelastic
            self.save_to_jelastic()
            # Fetches, to verify changes were proceeded with correctly
            self.refresh_from_api()
        # Make extra sure we did update everything needed, and that all sub saves behaved correctly
        assertmsg = f" {self.__class__.__name__}: save_to_jelastic() method only partially implemented."
        assert not self.differs_from_api(), assertmsg


class JelasticEnvironment(_JelasticObject):
    """
    Represents a Jelastic Environment
    """

    _jelattributes = [
        "displayName",
        "envGroups",
    ]
    _readonly_jelattributes = [
        "envName",
        "shortdomain",
        "domain",
    ]

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
