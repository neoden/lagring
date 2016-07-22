# Lagring: asset storage for Flask


## Requirements

- SQLAlchemy
- Flask
- PostgreSQL 9.4+

## Installation

    pip install lagring

If you want to use `ImageAsset` class you have to install Pillow as well.

## How to use it

0. Configure your Flask app to have necessary config options:

    Parameter          | Meaning
    -------------------|--------------------------------------------------
    ASSET_STORAGE_ROOT | Path to the directory where assets will be stored
    ASSET_URL_ROOT     | Asset URL invariable part

1.  Create storage instance:

    ```python
        from lagring import FlaskLagring

        storage = FlaskLagring()
        storage.init_app(app)
    ```

2. Derive your SQLAlchemy model from `storage.Entity` class:

    ```python
        from lagring import Asset

        class File(db.Model, storage.Entity):
            id = db.Column(db.Integer, primary_key=True)
            file = Asset()
    ```

    Note that JSONB field `_assets` will be added to the model (PostgreSQL 9.4+).
    You can change the name by overriding `lagring.Entity.asset_data_field` method.

3. Put something to that asset field:

    ```python
        new_file = File()
        db.session.add(new_file)
        db.session.flush()
        new_file.file = '/some/local/path/filename'
        db.session.commit()
    ```

    The model instance must have a valid id on asset assignment, so you have to call `flush()`
    before that.

4. Then you can use the asset like this:

    ```python
        # get asset URL
        url = new_file.file.url
        # get asset path
        path = new_file.file.abs_path
        # delete the asset
        del new_file.file
    ```

## More asset classes

- lagring.assets.**ImageAsset**(_size_=None, _width_=None, _height_=None, _transform_='crop', _constraint_type_='none', _size_constraint_=None, _init_lazy_=None)

    Image asset is always converted to PNG unless it is JPEG. 
    
    - **size** - target size
    - **width** - target width
    - **height** - target height
    
        If asset size is set only by width or height then target size is calculated using image aspect ratio.
    - **transform** - process method
        - 'crop' - resize and crop to size
        - 'fit' - fit to size, preserving the original aspect ratio
    - **constraint_type** - size constraint type:
        - 'none' - no constraint
        - 'min' - minimum size is set
        - 'max' - maximum size is set
        - 'exact' - exact target size is set
        
        If the size constraint is not met, the `AssetRequirementsException` will be thrown.
        Process method set in _transform_ parameter will be also taken into account.
    - **size_constraint** - size constraint value
    - **lazy_init** - specify callable to return asset parameters. Typical usecase —
        setup asset using parameters specified in the application config. Asset
        will be initialized on first access.
    
    
- lagring.assets.**DirectoryAsset**()

    Asset type to store directory assets. Source can be a directory or zip archive which is unpacked upon upload to the storage.
    
    
## Exceptions

- **StorageException**

    General purpose "something gone wrong with the storage" error. 
    
- **AssetRequirementsException**
 
    Data being uploaded does not meet requirements configured for asset field.
     
- **AssetProcessingException**

    Error while processing asset data.