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
    TokenUnauthorizedError, PasswordAuthTokenApiHandler, FixedTokenApiHandler, EnvironmentTokenApiHandler

from hiro_graph_client.version import __version__

this_directory = path.abspath(path.dirname(__file__))

__all__ = [
    'HiroGraph', 'HiroAuth', 'HiroApp', 'HiroGraphBatch', 'SessionData',
    'HiroResultCallback', 'AbstractTokenApiHandler', 'PasswordAuthTokenApiHandler', 'FixedTokenApiHandler',
    'EnvironmentTokenApiHandler', 'AuthenticationTokenError', 'FixedTokenError', 'TokenUnauthorizedError',
    'AbstractIOCarrier', 'BasicFileIOCarrier', 'SourceValueError', '__version__'
]

site.addsitedir(this_directory)
