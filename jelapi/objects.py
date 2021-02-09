from abc import ABC, abstractmethod
from copy import deepcopy

from .exceptions import JelasticObjectException


class _JelasticObject(ABC):
    """
    Any Jelastic Object, that keeps the last data as fetched from the API
    """

    _jelattributes = []
    _readonly_jelattributes = []
    _from_api = None

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
            raise AttributeError(f"'{name}' is read only in this JelasticObject.")
        object.__setattr__(self, name, value)

    def copy_self_as_from_api(self) -> None:
        """
        Store a copy of ourselves, as it was from API
        """
        self._from_api = deepcopy(self)
        # Verify the attributes got copied correctly
        for jelattribute in self._jelattributes:
            # First, they exist
            assert getattr(self, jelattribute)
            # They got copied correctly
            assert getattr(self, jelattribute) == getattr(self._from_api, jelattribute)

    def differs_from_api(self) -> bool:
        for jelattribute in self._jelattributes:
            if getattr(self, jelattribute) != getattr(self._from_api, jelattribute):
                return True
        for jelattribute in self._jelattributes:
            if getattr(self, jelattribute) != getattr(self._from_api, jelattribute):
                return True

    @abstractmethod
    def save(self) -> None:
        pass


class JelasticEnvironment(_JelasticObject):
    """
    Represents a Jelastic Environment
    """

    _jelattributes = [
        "displayName",
    ]
    _readonly_jelattributes = [
        "envName",
        "shortdomain",
        "domain",
    ]

    def __init__(self, *, from_GetEnvInfo: {}) -> None:
        """
        Construct a JelasticEnvironment from various data sources
        """
        super().__init__()

        if from_GetEnvInfo:
            if "result" not in from_GetEnvInfo:
                raise JelasticObjectException("'result' not returned from GetEnvInfo.")
            if from_GetEnvInfo["result"] != 0:
                raise JelasticObjectException("'result' not 0 from GetEnvInfo.")

            """
            Construct our object from the structure
            """
            # Allow exploration of the returned object, but don't act on it.
            self._envinfo = from_GetEnvInfo
            # Read-only attributes
            self._shortdomain = self._envinfo["env"]["shortdomain"]
            self._envName = self._envinfo["env"]["envName"]
            self._domain = self._envinfo["env"]["domain"]

            # Read-write attributes
            self.displayName = self._envinfo["env"]["displayName"]

        # Copy our attributes as it came from API
        self.copy_self_as_from_api()

    def __str__(self) -> str:
        return f"JelasticEnvironment '{self.envName}' <https://{self.domain}>"

    def _save_displayName(self):
        if self.displayName != self._from_api.displayName:
            raise JelasticObjectException("displayName should be updated")

    def save(self) -> bool:
        if not self.differs_from_api():
            return True

        self._save_displayName()
