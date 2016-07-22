# coding=utf-8

class StorageException(Exception):
    """
    Storage-specific exception
    """
    pass



class AssetRequirementsException(StorageException):
    """
    Requirements for the asset data not met
    """
    pass


class AssetProcessingException(StorageException):
    """
    Error when processing asset data
    """
    pass
