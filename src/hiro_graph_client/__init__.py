"""
Package which contains the classes to communicate with HIRO Graph.
"""
import site
from os import path

from hiro_graph_client.appclient import HiroApp
from hiro_graph_client.authclient import HiroAuth
from hiro_graph_client.batchclient import HiroGraphBatch, SessionData, AbstractIOCarrier, BasicFileIOCarrier, \
    SourceValueError, HiroResultCallback
from hiro_graph_client.client import HiroGraph
from hiro_graph_client.clientlib import AbstractTokenApiHandler, AuthenticationTokenError, FixedTokenError, \
    TokenUnauthorizedError, PasswordAuthTokenApiHandler, FixedTokenApiHandler, EnvironmentTokenApiHandler, \
    accept_all_certs

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'VERSION'), encoding='utf-8') as f:
    __version__ = f.read().strip()

__all__ = [
    'HiroGraph', 'HiroAuth', 'HiroApp', 'HiroGraphBatch', 'SessionData',
    'HiroResultCallback', 'AbstractTokenApiHandler', 'PasswordAuthTokenApiHandler', 'FixedTokenApiHandler',
    'EnvironmentTokenApiHandler', 'AuthenticationTokenError', 'FixedTokenError', 'TokenUnauthorizedError',
    'AbstractIOCarrier', 'BasicFileIOCarrier', 'SourceValueError', 'accept_all_certs', '__version__'
]

site.addsitedir(this_directory)
