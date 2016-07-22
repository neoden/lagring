from setuptools import setup, find_packages

setup(
    name="Lagring",
    version="0.2.4",
    author="Lenar Imamutdinov",
    author_email="lenar.imamutdinov@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/neoden/lagring",
    license="MIT",
    description="Asset storage for Flask",
    long_description=open("README.md").read(),
    install_requires=[
        "flask",
        "sqlalchemy"
    ],
    extras_require = {
        'Pillow': []
    }
)