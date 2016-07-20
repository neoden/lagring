import os
import zipfile
import shutil
from tempfile import gettempdir
from uuid import uuid4


from lagring import Asset, StorageException


class DirectoryAsset(Asset):
    """
    Asset type to store directory assets. Source can be a directory or zip archive which
    is unpacked upon upload to the storage.
    """
    def _get_temp_path(self):
        return os.path.join(gettempdir(), str(uuid4()))

    def _unzip(self, path, storage, meta):
        if zipfile.is_zipfile(path):
            temp_dir = self._get_temp_path()

            def cleanup():
                shutil.rmtree(temp_dir)

            with zipfile.ZipFile(path, 'r') as z:
                z.extractall(temp_dir)
                temp_src = storage.asset_source_adapter(temp_dir)
                return temp_src, meta, cleanup
        else:
            raise StorageException('Valid zip-archive expected')

    def upload(self, storage, src, meta=None):
        if src.type == 'directory':
            return src, meta, None
        elif src.type == 'file':
            return self._unzip(src.path, storage, meta)
        elif src.type == 'stream':
            temp_path = self._get_temp_path()
            with open(temp_path, 'wb') as f:
                shutil.copyfileobj(src.stream, f)
            new_src, _, cleanup = self._unzip(temp_path, storage, meta)

            def cleanup2():
                cleanup()
                os.remove(temp_path)

            return new_src, meta, cleanup2
        else:
            raise StorageException('Unknown source type')
