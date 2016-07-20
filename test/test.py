import os
import pytest

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


INSTANCE_ROOT = ''

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://lagring:lagring@localhost:5432/lagring_test'
app.config['ASSET_STORAGE_ROOT'] = os.path.join(os.getcwd(), 'test/var/assets')
app.config['ASSET_URL_ROOT'] = '/assets'

db = SQLAlchemy(app)

core = None
entity_base = None
model = None
instance = None
storage = None

IMAGE_PATH = os.path.join(INSTANCE_ROOT, 'test/data/image.jpg')
DIR_PATH = os.path.join(INSTANCE_ROOT, 'test/data')


def test_core():
    from lagring import LagringCore

    global core
    core = LagringCore(os.path.join(INSTANCE_ROOT, app.config['ASSET_STORAGE_ROOT']))


def test_model_definition():
    from lagring import Entity, Asset

    global entity_base
    entity_base = Entity
    entity_base.bind(core)

    class A(db.Model, entity_base):
        __tablename__ = 'test'

        id = db.Column(db.Integer(), primary_key=True)

        image = Asset()
        directory = Asset()

    global model
    model = A


def test_entity_type():
    from lagring import Entity, Asset

    class B(db.Model, Entity):
        __entitytype__ = 'special'
        __tablename__ = 'regular'

        id = db.Column(db.Integer(), primary_key=True)

        image = Asset()

    assert(B.entity_type == 'special')


def test_none_asset():
    with app.app_context():
        a = model(id=1)
        assert(not a.image)
        assert(not a.image.abs_path)

        global instance
        instance = a


def test_entity_id():
    assert(instance.entity_id == 1)


def test_write_to_model_field():
    with app.app_context():
        instance.image = IMAGE_PATH


def test_get_path_from_model():
    with app.app_context():
        assert(os.path.isfile(instance.image.abs_path))


def test_write_metadata():
    with app.app_context():
        instance.image = IMAGE_PATH, {'width': 100, 'height': 80}
        assert(instance.image.width == 100)
        assert(instance.image.height == 80)


def test_write_stream():
    with app.app_context():
        instance.image = open(IMAGE_PATH, 'rb')
        assert(os.path.isfile(instance.image.abs_path))


def test_delete_asset():
    from lagring.asset import NoneAssetInstance
    path = instance.image.abs_path
    del instance.image
    assert(isinstance(instance.image, NoneAssetInstance))


def test_write_directory():
    with app.app_context():
        instance.directory = DIR_PATH
        assert(os.path.isdir(instance.directory.abs_path))


def test_iterassets():
    with app.app_context():
        instance.image = IMAGE_PATH
        instance.directory = DIR_PATH

        n = 0
        assets = []

        for asset, name in instance.iterassets():
            n += 1
            assets.append((asset, name))
            assert(
                os.path.isfile(asset.abs_path)
                or
                os.path.isdir(asset.abs_path)
            )

        assert(assets[0][1] in ('image', 'directory'))
        assert(assets[1][1] in ('image', 'directory'))
        assert(assets[0][1] != assets[1][1])


def test_flask_lagring():
    from lagring import FlaskLagring

    global storage
    storage = FlaskLagring()
    storage.init_app(app)


def test_image_asset_def():
    from lagring.assets.image import ImageAsset

    class D(db.Model, storage.Entity):
        __tablename__ = 'test2'

        id = db.Column(db.Integer(), primary_key=True)

        image = ImageAsset(size=(100, 100))

    global model
    model = D


def test_image_asset():
    with app.app_context():
        a = model(id=1)
        assert(not a.image)
        assert(not a.image.abs_path)

        global instance
        instance = a


def test_image_asset_write():
    with app.app_context():
        instance.image = IMAGE_PATH
        assert(os.path.isfile(instance.image.abs_path))
        assert(instance.image.width == 100)
        assert(instance.image.height == 100)


def test_clone_assets():
    a = model(id=1)
    b = model(id=2)

    a.image = IMAGE_PATH
    storage.clone_assets(a, b)
    assert(os.path.isfile(a.image.abs_path))
    assert(os.path.isfile(b.image.abs_path))


def test_directory_asset_def():
    from lagring.assets.directory import DirectoryAsset

    class E(db.Model, storage.Entity):
        __tablename__ = 'test3'

        id = db.Column(db.Integer(), primary_key=True)

        directory = DirectoryAsset()

    global model
    model = E


def test_directory_asset():
    with app.app_context():
        a = model(id=1)
        assert(not a.directory)
        assert(not a.directory.abs_path)

        global instance
        instance = a


def test_directory_asset_write_directory():
    with app.app_context():
        instance.directory = os.path.join(DIR_PATH, 'directory_asset')
        assert(os.path.isdir(instance.directory.abs_path))
        assert(os.path.isfile(os.path.join(instance.directory.abs_path, 'image.jpg')))


def test_directory_asset_write_zip():
    with app.app_context():
        b = model(id=2)
        b.directory = os.path.join(DIR_PATH, 'image.jpg.zip')
        assert(os.path.isdir(instance.directory.abs_path))
        assert(os.path.isfile(os.path.join(instance.directory.abs_path, 'image.jpg')))


def test_directory_asset_write_invalid_zip():
    from lagring import StorageException

    with pytest.raises(StorageException) as excinfo:
        with app.app_context():
            c = model(id=3)
            c.directory = os.path.join(DIR_PATH, 'image.jpg')

    assert 'Valid zip-archive expected' in str(excinfo.value)


def test_directory_asset_write_zip_from_stream():
    from werkzeug.datastructures import FileStorage
    with app.app_context():
        d = model(id=4)
        with open(os.path.join(DIR_PATH, 'image.jpg.zip'), 'rb') as stream:
            d.directory = FileStorage(stream, 'image.jpg.zip')
        assert (os.path.isdir(instance.directory.abs_path))
        assert (os.path.isfile(os.path.join(instance.directory.abs_path, 'image.jpg')))
