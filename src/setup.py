from setuptools import setup, find_packages
from hiro_graph_client import __version__

setup(
    name="hiro_graph_client",
    version=__version__,
    packages=find_packages(),

    python_requires='>=3.7',
    
    install_requires=[
        'requests',
        'backoff'
    ],
   
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
    ]
)
