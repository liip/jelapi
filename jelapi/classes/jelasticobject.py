from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Dict, Any


class _JelasticAttribute:
    """
    Descriptor class, with two tweakables:
    - read_only
    - checked_for_differences
    """

    def __init__(self, read_only: bool = False, checked_for_differences: bool = True):
        self.read_only = read_only
        self.checked_for_differences = checked_for_differences

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = f"_{name}"

    def __get__(self, obj: Any, objtype: type = None) -> Any:
        return getattr(obj, self.private_name)

    def __set__(self, obj: Any, value: Any):

        if self.read_only:
            raise AttributeError(
                f"{self.__class__.__name__}: '{self.public_name}' is read only."
            )
        self.typecheck(value)
        setattr(obj, self.private_name, value)

    def typecheck(self, value: Any) -> None:
        """
        :raises TypeError if the typecheck fails
        """
        pass


class _JelAttrStr(_JelasticAttribute):
    def typecheck(self, value: Any) -> None:
        if not isinstance(value, str):
            raise TypeError


class _JelAttrInt(_JelasticAttribute):
    def typecheck(self, value: Any) -> None:
        if not isinstance(value, int):
            raise TypeError


class _JelAttrList(_JelasticAttribute):
    def typecheck(self, value: Any) -> None:
        if not isinstance(value, list):
            raise TypeError


class _JelasticObject(ABC):
    """
    Any Jelastic Object, that keeps the last data as fetched from the API
    _from_api                dict of attributes as last refreshed from API
    """

    _from_api: Dict[str, Any] = {}

    def copy_self_as_from_api(self) -> None:
        """
        Store a copy of ourselves, as it was from API
        """
        for k, v in vars(self).items():
            if k[0] == "_":
                # Check public_name
                k = k[1:]
            # This convoluted syntax checks if self.k is a _JelasticAttribute
            # These are the only ones we want to copy
            try:
                descriptor_class = vars(type(self))[k]
                if (
                    isinstance(descriptor_class, _JelasticAttribute)
                    and not descriptor_class.read_only
                ):
                    self._from_api[k] = deepcopy(v)
            except KeyError:
                pass
        # TODO Add an "updated_at" attribute

    def differs_from_api(self) -> bool:
        for k, v in vars(self).items():
            if k[0] == "_":
                # Check public_name
                k = k[1:]
            # This convoluted syntax checks if self.k is a _JelasticAttribute
            # These are the only ones we want to copy
            try:
                descriptor_class = vars(type(self))[k]
                if (
                    isinstance(descriptor_class, _JelasticAttribute)
                    and not descriptor_class.read_only
                    and descriptor_class.checked_for_differences
                    and self._from_api[k] != v
                ):
                    return True
            except KeyError:
                pass
        return False

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

    def save(self) -> None:
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
