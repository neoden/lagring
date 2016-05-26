# coding=utf-8

import os
import io
import shutil
import uuid

from .classproperty import classproperty
from .exception import StorageException
from .logger import log


class _AssetSource:
    def __init__(self, src, extension=None):
        self.src = src
        self.extension = self._normalise_extension(extension)

    @staticmethod
    def _normalise_extension(extension):
        if extension:
            return extension if extension[:1] == '.' else '.' + extension
        else:
            return ''

    def __bool__(self):
        return self.type is not None

    @property
    def type(self):
        if self.src is None:
            return None
        elif isinstance(self.src, str):
            if os.path.isfile(self.src):
                return 'file'
            elif os.path.isdir(self.src):
                return 'directory'
            else:
                raise StorageException('Path not found')
        elif isinstance(self.src, io.IOBase):
            return 'stream'
        else:
            raise StorageException('Unknown source type')

    @property
    def stream(self):
        if self.src is None:
            return None
        elif isinstance(self.src, str):
            if os.path.isfile(self.src):
                return open(self.src, 'rb')
            else:
                raise StorageException('File not found')
        elif isinstance(self.src, io.IOBase):
            return self.src
        else:
            raise StorageException('Unknown source type')

    @property
    def path(self):
        if isinstance(self.src, str):
            if os.path.isfile(self.src) or os.path.isdir(self.src):
                return self.src
        else:
            return None


class LagringCore(object):
    '''
    Storage base functionality
    '''

    def __init__(self, root, url_base='', write_allowed=True):
        '''
        root            - file storage base directory
        url_base        - URL base
        write_allowed   - set this to False for read-only access
        '''

        self.url_base = url_base
        self.root = root
        self.write_allowed = write_allowed

        if not os.path.exists(self.root):
            os.makedirs(self.root)
            log.info('Storage root has been created in "{}"'.format(self.root))

    @classproperty
    def asset_source_adapter(cls):
        return _AssetSource

    def _put(self, src, bucket, filename):
        '''
        Save asset file
        src - source
        bucket - storage directory
        filename - filename without directory
        '''
        bucket_path = os.path.join(self.root, bucket)
        if not os.path.exists(bucket_path):
            os.makedirs(bucket_path)

        dest_path = os.path.join(bucket_path, filename)

        type = src.type
        if type == 'file':
            shutil.copy(src.path, dest_path)
        elif type == 'directory':
            shutil.copytree(src.path, dest_path)
        elif type == 'stream':
            with open(dest_path, 'wb') as dest_obj:
                shutil.copyfileobj(src.stream, dest_obj)

        asset_path = os.path.join(bucket, filename)
        log.debug('Added "{}"'.format(asset_path))

        return asset_path

    def _trash(self, asset_path):
        '''
        Delete file
        '''
        abs_path = self.abs_path(asset_path)
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        elif os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        else:
            log.warning('Non-existent path to delete "{}"'.format(asset_path))
            return
        log.debug('Deleted "{}"'.format(asset_path))

    def _bucket(self, entity_type, entity_id, asset_name):
        '''
        Storage bucket path
        '''
        hex = '{0:0{1}x}'.format(entity_id, 8)
        return '{}/{}/{}/{}/{}'.format(entity_type, asset_name, hex[0:2], hex[2:4], hex[4:6])

    def add(self, entity_type, entity_id, asset_name, src):
        '''
        Add file or directory to the storage
        New filename contains random part so the old version must be explicitly deleted
        Returns path to the asset
        '''

        if not self.write_allowed:
            raise StorageException("Storage is in read-only mode")

        # генерим путь к ассету
        bucket = self._bucket(entity_type, entity_id, asset_name)
        filename = '{}-{}{}'.format(
            entity_id,
            str(uuid.uuid4())[:6],  # some random
            src.extension)

        asset_path = self._put(src, bucket, filename)

        log.debug(
            'Asset added: entity=({}, {}), asset_name={}'\
                .format(entity_type, entity_id, asset_name))

        return asset_path

    def delete(self, path):
        '''
        Delete asset
        '''

        if not self.write_allowed:
            raise StorageException("Storage is in read-only mode")

        self._trash(path)

    def url(self, path):
        '''
        Get asset URL
        '''

        return self.url_base + \
                   ('' if self.url_base.endswith('/') else '/') + \
                   path

    def abs_path(self, path):
        '''
        Get asset absolute path
        '''
        return os.path.join(self.root, path)
