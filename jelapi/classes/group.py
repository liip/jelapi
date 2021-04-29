from enum import Enum
from functools import lru_cache
from json import dumps as jsondumps
from typing import Any, Dict

from ..exceptions import JelasticObjectException
from .jelasticobject import _JelasticAttribute as _JelAttr
from .jelasticobject import (
    _JelasticObject,
    _JelAttrBool,
    _JelAttrHexColor,
    _JelAttrInt,
    _JelAttrStr,
)


class JelasticEnvGroup(_JelasticObject):
    """
    Represents a Jelastic Environment Group
    """

    class Visibility(Enum):
        """
        Standard Visibilities
        https://docs.jelastic.com/api/#!/api/environment.Group-method-CreateGroup
        """

        SHOW = 0
        HIDE = 1
        SHOW_IF_NOT_EMPTY = 2

    id = _JelAttrInt(read_only=True)
    name = _JelAttrStr(read_only=True)
    color = _JelAttrHexColor()
    isIsolated = _JelAttrBool()
    visibility = _JelAttr()

    def __init__(self, *, name: str = None, color: str = None):
        super().__init__()

        # Instantiate some empty, or default
        self._id = 0
        self.isIsolated = False
        self.visibility = self.Visibility.SHOW

        self._name = name
        self.color = color

        if name or color:
            assert not self.is_from_api
            assert self.differs_from_api()

    def update_from_api_dict(self, api_dict=Dict[str, Any]) -> None:
        """
        Update a JelasticEnvGroup from an API answer
        """
        self._group = api_dict
        # RO attributes
        self._id = self._group["id"]
        self._name = self._group["name"]
        # RW attributes
        self.color = self._group.get("color", None)
        self.isIsolated = self._group["isIsolated"]
        self.visibility = next(
            (v for v in self.Visibility if v.value == self._group["visibility"]),
            self.Visibility.SHOW,
        )
        self.copy_self_as_from_api()

    @staticmethod
    @lru_cache(maxsize=1)
    def dict() -> Dict[str, "JelasticEnvGroup"]:
        """
        Static method to get all Environment Groups
        """
        # This is needed as it's a static method
        from .. import api_connector as jelapi_connector

        response = jelapi_connector()._("Environment.Group.GetGroups")

        groups = {}
        for group in response["array"]:
            jeg = JelasticEnvGroup()
            jeg.update_from_api_dict(group)
            groups[jeg.name] = jeg

        return groups

    @staticmethod
    def get(name: str):
        """
        Get one envGroup object
        """
        try:
            return JelasticEnvGroup.dict()[name]
        except KeyError:
            raise JelasticObjectException(
                f"JelasticEnvGroup {name} doesn't exist. Perhaps refresh with JelasticEnvGroup.dict.cache_clear()"
            )

    @property
    def children(self) -> Dict[str, "JelasticEnvGroup"]:
        """
        This envGroup' children envGroups
        """
        return {
            k: eg
            for (k, eg) in JelasticEnvGroup.dict().items()
            if eg.name.startswith(f"{self.name}/")
        }

    def save_to_jelastic(self):
        """
        Save write'eable attributes
        """
        data = {}
        for attr in ["color", "isIsolated", "visibility"]:
            v = getattr(self, attr)
            if (
                not self._from_api
                or attr not in self._from_api
                or self._from_api[attr] != v
            ):
                if v:
                    data[attr] = v
                    if attr == "visibility":
                        data[attr] = v.value

        if self.is_from_api:
            self.api._(
                "Environment.Group.EditGroup",
                groupName=self.name,
                data=jsondumps(data),
            )
        else:
            self.api._(
                "Environment.Group.CreateGroup",
                groupName=self.name,
                data=jsondumps(data),
            )
        self.copy_self_as_from_api()
        assert not self.differs_from_api()

    def delete_from_api(self):
        """
        Delete envGroup from API
        """
        self.api._(
            "Environment.Group.RemoveGroup",
            groupName=self.name,
        )
        delattr(self, "_from_api")
