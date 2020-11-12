"""
Package which contains the classes to communicate with HIRO / Graphit.
"""
import site
from os import path

from hiro_graph_client.batchclient import GraphitBatch, SessionData, AbstractIOCarrier, SourceValueError, ResultCallback
from hiro_graph_client.client import Graphit, AuthenticationTokenError, accept_all_certs

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'VERSION'), encoding='utf-8') as f:
    __version__ = f.read().strip()

__all__ = [
    'Graphit', 'GraphitBatch', 'SessionData', 'ResultCallback',
    'AuthenticationTokenError', 'AbstractIOCarrier',
    'SourceValueError', 'accept_all_certs', '__version__'
]

site.addsitedir(this_directory)
