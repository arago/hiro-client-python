"""
Package which contains the classes to communicate with HIRO / Graphit.
"""
import site
from os.path import dirname

from hiro_client.batchclient import GraphitBatch, SessionData, AbstractIOCarrier, SourceValueError, ResultCallback
from hiro_client.client import Graphit, AuthenticationTokenError, accept_all_certs

__version__ = "2.4.0"

__all__ = [
    'Graphit', 'GraphitBatch', 'SessionData', 'ResultCallback',
    'AuthenticationTokenError', 'AbstractIOCarrier',
    'SourceValueError', 'accept_all_certs'
]

site.addsitedir(dirname(__file__))
