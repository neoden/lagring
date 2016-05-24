from .exception import StorageException


class AssetInstance:
    def __init__(self, url, path, abs_path, meta):
        self.url = url
        self.path = path
        self.abs_path = abs_path
        self.meta = meta

    def __bool__(self):
        return True

    def __getattr__(self, name):
        if name in self.meta:
            return self.meta[name]


class NoneAssetInstance:
    def __init__(self):
        self.url = None
        self.path = None
        self.abs_path = None
        self.meta = None

    def __bool__(self):
        return False


class Asset:
    def __get__(self, entity, entity_cls=None):
        if entity:
            # access from entity instance - return asset instance object
            return self._asset_instance(entity)
        else:
            # access from entity class - return asset definition object
            return self

    def __set__(self, entity, value):
        # split value to asset source and metadata dictionary
        if isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError('Tuple of two elements expected')
            src, meta = value
        else:
            src, meta = value, None

        storage = entity.storage

        asset_source = storage.asset_source_adapter(src)
        if not asset_source:
            # empty asset sources are ignored
            return
        asset_source, meta, when_done = self.upload(storage, asset_source, meta)

        # delete existing asset if any
        asset = self._asset_instance(entity)
        if asset:
            storage.delete(asset.path)

        entity_type = entity.entity_type
        entity_id = entity.entity_id
        if not entity_id:
            raise StorageException('Entity does not have an id. Probably you forgot to flush before asset assignment.')
        asset_name = entity._asset_name(self)

        data = {
            'path': storage.add(entity_type, entity_id, asset_name, asset_source)
        }
        # append metadata fields
        if meta:
            for k, v in meta.items():
                data[k] = v

        # put to database
        entity.put_asset_data(asset_name, data)

        if when_done:
            when_done()

    def __delete__(self, entity):
        asset = self._asset_instance(entity)
        if asset:
            asset_name = entity._asset_name(self)
            entity.storage.delete(asset.path)
            entity.put_asset_data(asset_name, {})

    def _asset_instance(self, entity):
        """
        Build asset instance object from entity
        """
        name = entity._asset_name(self)
        value = entity.get_asset_data(name)
        if value:
            path = value['path']
            asset = AssetInstance(
                path=path,
                url=entity.storage.url(path),
                abs_path=entity.storage.abs_path(path),
                meta=value
            )
            return asset
        else:
            return NoneAssetInstance()

    def upload(self, storage, src, meta=None):
        """
        Preprocess file before actual loading to storage.
        Returns path to new file, altered/created metadata and when_done callable
        to be called when everything is done (to perform some cleanup if needed)
        
        """
        return src, meta, None

    def after_upload(self, storage, asset):
        """
        Post-process file after upload to storage
        """
        pass