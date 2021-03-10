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
