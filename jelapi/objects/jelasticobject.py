from abc import ABC, abstractmethod
from copy import deepcopy


class _JelasticObject(ABC):
    """
    Any Jelastic Object, that keeps the last data as fetched from the API
    _jelattributes           array of string attribute names that can be modified in that object
    _readonly_jelattributes  array of string attribute names that cannot be modified (but accessed) in that object
    _from_api                dict of attributes as last refreshed from API
    """

    _jelattributes = []
    _readonly_jelattributes = []
    _from_api = {}

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
        # TODO Add an "updated_at" attribute

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

    @property
    def api(self):
        """
        Return the global api connector, as property
        """
        from .. import api_connector as jelapi_connector

        return jelapi_connector()

    @staticmethod
    @abstractmethod
    def get(*kwargs):
        """
        Static method to get a instance of this class
        """
