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

5. Besides the basic `Asset` class, there are also `ImageAsset` and `DirectoryAsset` to store
something more specific and have some processing on upload (no docs for that yet, please see
the code).
