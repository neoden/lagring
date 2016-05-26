from setuptools import setup, find_packages

setup(
    name="Lagring",
    version="0.1.3",
    author="Lenar Imamutdinov",
    author_email="lenar.imamutdinov@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/neoden/lagring",
    license="MIT",
    description="Asset storage for Flask",
    long_description=open("README.txt").read(),
    install_requires=[
        "flask",
    ],
    extras_require = {
        'Pillow': []
    }
)