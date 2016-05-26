import os

from werkzeug.datastructures import FileStorage

from .core import LagringCore, _AssetSource
from .entity import Entity
from .classproperty import classproperty
from .exception import StorageException


class _AssetSourceEx(_AssetSource):
    @property
    def type(self):
        if isinstance(self.src, FileStorage):
            if self.src.filename != '':
                return 'stream'
            else:
                return None
        else:
            return super().type

    @property
    def stream(self):
        if isinstance(self.src, FileStorage):
            if self.src.filename != '':
                return self.src.stream
            else:
                return None
        else:
            return super().stream


class FlaskLagring(LagringCore):
    def __init__(self):
        pass

    def init_app(self, app):
        root = app.config['ASSET_STORAGE_ROOT']
        if root[:1] != '/':
            raise StorageException('ASSET_STORAGE_ROOT path must be absolute')
        self.setup(
            root=root,
            url_base=app.config['ASSET_URL_ROOT'],
            write_allowed=True
        )

    def setup(self, root, url_base='', write_allowed=True):
        '''
        root            - file storage base directory
        url_base        - URL base
        write_allowed   - set this to False for read-only access
        '''
        LagringCore.__init__(self, root, url_base, write_allowed)

    @property
    def Entity(self):
        '''
        Asset-aware entity mixin class
        '''
        base = Entity
        base.bind(self)
        return base

    @classproperty
    def asset_source_adapter(cls):
        return _AssetSourceEx

    def clone_assets(self, src_entity, dest_entity):
        for asset, name in src_entity.iterassets():
            self.add(
                src_entity.entity_type, 
                dest_entity.id, 
                name, 
                self.asset_source_adapter(asset.abs_path)
            )
            data = src_entity.get_asset_data(name)
            dest_entity.put_asset_data(name, data)
