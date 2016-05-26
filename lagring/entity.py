from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import Column

from .classproperty import classproperty
from .exception import StorageException
from .asset import Asset


class Entity:
    """
    Base class for asset-aware models
    """

    @declared_attr
    def _assets(self):
        return Column(JSONB)

    @classmethod
    def _build_asset_name_table(cls):
        if not hasattr(cls, '__asset_names'):
            fields = {}
            for name in dir(cls):
                if not name.startswith('_'):
                    asset_field = getattr(cls, name)
                    if isinstance(asset_field, Asset):
                        fields[asset_field] = name
            cls.__asset_names = fields

    @classproperty
    def _asset_names(cls):
        try:
            return cls.__asset_names
        except AttributeError:
            cls._build_asset_name_table()
            return cls.__asset_names

    @classmethod
    def _asset_name(cls, asset_def_obj):
        """
        Find asset name by asset definition object
        """
        try:
            return cls._asset_names[asset_def_obj]
        except KeyError:
            raise StorageException('Asset name not found')

    @classmethod
    def bind(cls, storage):
        """
        Late binding to storage instance
        """
        cls.__storage = storage

    @classproperty
    def storage(cls):
        """
        Storage instance
        """
        return cls.__storage

    @classproperty
    def entity_type(cls):
        """
        Unique entity type name. Specified by __entitytype__ or __tablename__.
        """
        if hasattr(cls, '__entitytype__'):
            return getattr(cls, '__entitytype__')
        elif hasattr(cls, '__tablename__'):
            return getattr(cls, '__tablename__')
        else:
            raise StorageException('Unknown entity type. Neither __entitytype__ nor __tablename__ are defined in the model.')

    @property
    def entity_id(self):
        """
        Return model id field. It is highly recommended to have an integer id field.
        """
        try:
            if self.id:
                return self.id
            raise StorageException('No entity id')
        except AttributeError:
            raise StorageException('No "id" column found. You might wish to override entity_id to handle non-trivial primary key fields.')

    def iterassets(self):
        """
        Iterate of entity instance assets
        """
        return ((getattr(self, name), name) for asset, name in self._asset_names.items())

    def asset_data_field(self, asset_name):
        """
        Return model field name that contains asset data for that asset name.
        Everything is stored in _assets field by default
        """
        return '_assets'

    def get_asset_data(self, name):
        """
        Extract given asset data from the model field
        """
        value = getattr(self, self.asset_data_field(name)) or {}
        return value.get(name)

    def put_asset_data(self, name, data):
        """
        Write asset data to the model field
        """
        field_name = self.asset_data_field(name)
        value = getattr(self, field_name) or {}
        value[name] = data
        setattr(self, field_name, dict(value))
        # without that JSON fields are not updated in commit
        flag_modified(self, field_name)
