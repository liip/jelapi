from warnings import warn


class JelapiException(Exception):
    """
    Generic Jelapi Exception
    """

    pass


class JelasticAPIException(JelapiException):
    """
    Low-level API Exception
    """

    pass


class JelasticObjectException(JelapiException):
    """
    Object instanciation issue
    """

    pass


def deprecation(message: str) -> None:
    """
    Announce deprecated argumets, functions, classes
    """
    warn(message, DeprecationWarning, stacklevel=2)
