import logging

from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict


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
            raise TypeError(f"{value} is no str")


class _JelAttrBool(_JelasticAttribute):
    def typecheck(self, value: Any) -> None:
        if not isinstance(value, bool):
            raise TypeError(f"{value} is no bool")


class _JelAttrInt(_JelasticAttribute):
    def typecheck(self, value: Any) -> None:
        if not isinstance(value, int):
            raise TypeError(f"{value} is no int")


class _JelAttrDatetime(_JelasticAttribute):
    def typecheck(self, value: Any) -> None:
        if not isinstance(value, datetime):
            raise TypeError(f"{value} is no datetime")


class _JelAttrDict(_JelasticAttribute):
    def typecheck(self, value: Any) -> None:
        if not isinstance(value, dict):
            raise TypeError(f"{value} is no dict")
        # Checking the dict _items_ for type doesn't work, see List


class _JelAttrList(_JelasticAttribute):
    def typecheck(self, value: Any) -> None:
        if not isinstance(value, list):
            raise TypeError(f"{value} is no list")
        # Checking the list _items_ for type doesn't work reliably; one can l.append(item) and it won't be checked


class _JelAttrIPv4(_JelAttrStr):
    def typecheck(self, value: Any) -> None:
        super().typecheck(value)
        ip_chunks = value.split(".")
        if len(ip_chunks) != 4:
            raise TypeError(f"{value} is no IPv4 address")
        for n in ip_chunks:
            try:
                if int(n) < 0 or int(n) > 255:
                    raise TypeError(f"{value} is no IPv4 address ({n} is out of range)")
            except ValueError:
                raise TypeError(f"{value} is no IPv4 address ({n} is no int)")


class _JelasticObject(ABC):
    """
    Any Jelastic Object, that keeps the last data as fetched from the API
    _from_api                dict of attributes as last refreshed from API
    """

    _from_api: Dict[str, Any] = None
    _logger: logging.Logger

    def __init__(self, *args, **kwargs) -> None:
        """
        Instantiate logger
        """
        self._logger = logging.getLogger(self.__class__.__name__)

    def _tracelog(self, msg, *args, **kwargs):
        """
        Coding-level tracer, if needed
        """
        return self._logger.log(logging.DEBUG - 1, msg, *args, **kwargs)

    def copy_self_as_from_api(self, only_this_key: str = None) -> None:
        """
        Store a copy of ourselves, as it was from API
        """
        # Instantiate dict
        if not self._from_api:
            self._from_api = {}
        for k, v in vars(self).items():
            if k[0] == "_":
                # Check public_name
                k = k[1:]
            if only_this_key and k != only_this_key:
                # Only handle one key, and it's not this one
                continue
            # This convoluted syntax checks if self.k is a _JelasticAttribute
            # These are the only ones we want to copy
            try:
                descriptor_class = vars(type(self))[k]
            except KeyError:
                descriptor_class = None

            if (
                isinstance(descriptor_class, _JelasticAttribute)
                and not descriptor_class.read_only
            ):
                self._from_api[k] = deepcopy(v)

        self._from_api["copied_to_api_at"] = datetime.now()

    @property
    def is_from_api(self) -> bool:
        """
        Whether it was from API or is a new instance
        """
        try:
            return hasattr(self, "_from_api") and "copied_to_api_at" in self._from_api
        except TypeError:
            return False

    def differs_from_api(self) -> bool:
        """
        Check if the JelasticAttributes differ from the API
        """
        if not self.is_from_api:
            return True

        for k, v in vars(self).items():
            if k[0] == "_":
                # Check public_name
                k = k[1:]
            # This convoluted syntax checks if self.k is a _JelasticAttribute
            # These are the only ones we want to copy
            try:
                descriptor_class = vars(type(self))[k]
            except KeyError:
                descriptor_class = None
            if (
                isinstance(descriptor_class, _JelasticAttribute)
                and not descriptor_class.read_only
            ):
                if descriptor_class.checked_for_differences:
                    if k not in self._from_api or self._from_api[k] != v:
                        return True
                elif isinstance(descriptor_class, _JelAttrList):
                    if len(v) != len(self._from_api[k]):
                        return True
                    if any(item.differs_from_api() for item in v):
                        return True
                elif isinstance(descriptor_class, _JelAttrDict):
                    if len(v) != len(self._from_api[k]):
                        return True
                    if any(item.differs_from_api() for item in v.values()):
                        return True
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
