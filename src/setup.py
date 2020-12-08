import datetime
from os import path

from hiro_graph_client import __version__
from setuptools import setup, find_packages

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

subversion = datetime.datetime.now(tz=datetime.timezone.utc).strftime('%Y%m%d%H%M%S')

setup(
    name="hiro_graph_client",
    version=__version__,
    packages=find_packages(),

    python_requires='>=3.7',

    install_requires=[
        'requests',
        'backoff'
    ],
    package_data={
        'hiro_graph_client': ['VERSION']
    },

    author="arago GmbH",
    author_email="info@arago.co",
    maintainer="Wolfgang Hübner",
    description="Hiro Client for Graph REST API of HIRO 7",
    keywords="HIRO7 arago GraphIt REST API",
    url="https://github.com/arago/python-hiro-clients",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    long_description=long_description,
    long_description_content_type='text/markdown'
)
