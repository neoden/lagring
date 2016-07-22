import os
from tempfile import gettempdir
from uuid import uuid4

from PIL import Image

from lagring import Asset, StorageException, AssetRequirementsException, AssetProcessingException
from lagring.logger import log


class ImageAsset(Asset):
    """
    Asset type to store image files

    Supported parameters:

    size - target size
    width - target width
    height - target height
        If asset size is set only by width or height,
        target size is calculated using image aspect ratio.
    transform - process method
        'crop' - resize and crop to size
        'fit' - fit to size, preserving the original aspect ratio
    size_constraint - size constraint value (see below)
    constraint_type - size constraint type:
        'none' - no constraint
        'min' - minimum size is set
        'max' - maximum size is set
        'exact' - exact target size is set
        If the size constrain is not met, the StorageException will be thrown.
        Process method set in "transform" will be also taken into account.
    lazy_init - specify callable to return asset parameters. Typical usecase --
        setup asset using parameters specified in the application config. Asset
        will be initialized on first access.
    """
    def __init__(self, init_lazy=None, **kwargs):
        if init_lazy:
            self.init_lazy = init_lazy
        else:
            self._init(**kwargs)

    def _init(self, size=None, width=None, height=None,
              transform='crop', size_constraint=None, constraint_type='none'):
        if transform not in ('crop', 'fit'):
            raise ValueError('Unknown transformation type')

        self.size = size
        self.width = width
        self.height = height

        if size:
            if height or width:
                raise StorageException('Use either size or width/height')
            else:
                self.width, self.height = self.size
        elif width and height:
            self.size = (width, height)

        self.transform = transform
        self.size_constraint = size_constraint
        self.constraint_type = constraint_type

        if constraint_type != 'none':
            if size_constraint:
                self.size_constraint = size_constraint
            else:
                self.size_constraint = size
            self.constraint_type = constraint_type
        else:
            if size_constraint:
                raise StorageException('Size constraint is set but no constraint type is specified')

        self.init_lazy = None

    def __getattr__(self, item):
        if not self.init_lazy:
            # ленивая инициализация не задана, ничего не поделаешь
            raise AttributeError(item)
        else:
            self._init(**self.init_lazy())
            return getattr(self, item)

    def _target_size(self, original_size):
        if self.size:
            size = self.size
        else:
            width, height = original_size
            if self.width:
                height = int(height * (self.width / width))
                width = self.width
            elif self.height:
                width = int(width * (self.height / height))
                height = self.height
            size = width, height

        return size

    @staticmethod
    def _get_image_size(src):
        try:
            img = Image.open(src)
            return img.size
        except OSError:
            raise AssetProcessingException('Failed to open image')

    @staticmethod
    def _size_to_dict(size):
        '''
        (width, height) --> {'width': width, 'height': height}
        '''
        return {'width': size[0], 'height': size[1]}

    def _get_image_metadata(self, src):
        return self._size_to_dict(self._get_image_size(src))

    @staticmethod
    def _downsize_img(img, size, mode='crop'):
        if mode == 'crop':
            iw, ih = img.size
            width, height = size
            if iw > width or ih > height:
                iaspect = iw / ih
                taspect = width / height
                if iaspect > taspect:
                    left = int((iw - ih * taspect) / 2)
                    right = iw - left
                    crop_rect = (left, 0, right, ih)
                else:
                    upper = int((ih - iw / taspect) / 2)
                    lower = ih - upper
                    crop_rect = (0, upper, iw, lower)

                img = img.crop(crop_rect).resize(size, Image.BICUBIC)
        elif mode == 'fit':
            img.thumbnail(size, Image.BICUBIC)

        return img

    def _downsize(self, src, dest, size, mode='crop', force_name=False, force_format=None):
        """
        Crop and resize down to given size
        :param size: tuple (width, height)
        :param mode: crop - rezise and crop, fit - fit to size
        :return: modified image
        """
        try:
            img = Image.open(src)
        except OSError:
            raise AssetProcessingException('Failed to open image')

        format = img.format
        res_img = self._downsize_img(img, size, mode=mode)

        if force_format:
            new_format = force_format
        else:
            new_format = 'JPEG' if format == 'JPEG' else 'PNG'

        extension = new_format.lower()

        if force_name:
            new_path = dest
        else:
            new_path = dest + '.' + extension

        try:
            res_img.save(new_path, new_format)
        except OSError:
            raise AssetProcessingException('Failed to save temporary image')

        return new_path, extension

    @staticmethod
    def _get_temp_path(dir=None, ext=''):
        if ext and ext[:1] != '.':
            ext = '.' + ext
        return os.path.join(gettempdir() if dir is None else dir, str(uuid4()) + ext)

    def upload(self, storage, src, meta=None):
        original_size = self._get_image_size(src.stream)

        if self.constraint_type == 'min':
            if original_size[0] < self.size_constraint[0] or original_size[1] < self.size_constraint[1]:
                raise AssetRequirementsException('Size is less than minimum constraint')
        elif self.constraint_type == 'max':
            if original_size[0] > self.size_constraint[0] or original_size[1] > self.size_constraint[1]:
                raise AssetRequirementsException('Size is bigger than maxmimum constraint')
        elif self.constraint_type == 'exact':
            if original_size[0] != self.size_constraint[0] and original_size[1] != self.size_constraint[1]:
                raise AssetRequirementsException('Exact size constraint is not met')
        
        if not any([self.size, self.width, self.height]):
            # без обработки
            new_path = self._get_temp_path()
            if meta is None:
                meta = self._size_to_dict(original_size)

            try:
                img = Image.open(src.stream)
            except OSError:
                raise AssetProcessingException('Failed to open image')

            new_format = 'JPEG' if img.format == 'JPEG' else 'PNG'

            try:
                img.save(new_path, new_format)
            except OSError:
                raise AssetProcessingException('Failed to save temporary image')

            extension = new_format.lower()
        else:
            target_size = self._target_size(original_size)
            temp = self._get_temp_path()
            new_path, extension = self._downsize(src.stream, temp, target_size, self.transform)
            meta = self._get_image_metadata(new_path)
            log.debug(
                'Processing image: {} {}'.format(self.transform, target_size))

        new_src = storage.asset_source_adapter(new_path, extension=extension)

        def when_done():
            os.remove(new_path)

        return new_src, meta, when_done
