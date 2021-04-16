#!/usr/bin/env python3

from typing import Iterator
from urllib.parse import quote_plus

from hiro_graph_client.clientlib import HiroApiHandler, AuthenticatedAPI, AbstractTokenHandler


class HiroApp(AuthenticatedAPI):
    """
    Python implementation for accessing the HIRO App REST API.
    See https://core.arago.co/help/specs/?url=definitions/app.yaml
    """

    def __init__(self,
                 endpoint: str = None,
                 api_handler: HiroApiHandler = None,
                 token_handler: AbstractTokenHandler = None,
                 raise_exceptions: bool = False,
                 proxies: dict = None):
        """
        Constructor

        :param api_handler: Instance of a version handler that contains the current API endpoints.
        :param endpoint: Full url for app API. Overrides endpoints taken from *api_handler*.
        :param token_handler: External token handler. An internal one is created when this is unset.
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False
        :param proxies: Proxy configuration for *requests*. Default is None.
        """
        super().__init__(api_name='app',
                         api_handler=api_handler,
                         endpoint=endpoint,
                         token_handler=token_handler,
                         raise_exceptions=raise_exceptions,
                         proxies=proxies)

    ###############################################################################################################
    # REST API operations
    ###############################################################################################################

    def get_app(self, node_id) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}'`

        :param node_id: ogit/_id of the node/vertex or edge.
        :return: The result payload
        """
        url = self._endpoint + '/' + quote_plus(node_id)
        return self.get(url)

    def get_config(self) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/config'`. The token (internal or external) defines the config
        returned.

        :return: The result payload
        """
        url = self._endpoint + '/config'
        return self.get(url)

    def get_content(self, node_id, path) -> Iterator[bytes]:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}/content/{path}'`. Get the content of an application.

        :param node_id: ogit/_id of the node/vertex or edge.
        :param path: filename / path of the desired content.
        :return: The result payload yields over binary data.
        """
        url = self._endpoint + '/' + quote_plus(node_id) + '/content/' + quote_plus(path)
        yield self.get_binary(url)

    def get_manifest(self, node_id) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}/manifest'`. Get the manifest of an application.

        :param node_id: ogit/_id of the node/vertex or edge.
        :return: The result payload - usually with a binary content.
        """
        url = self._endpoint + '/' + quote_plus(node_id) + '/manifest'
        return self.get(url)

    def get_desktop(self) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/desktop'`. List desktop applications.

        :return: The result payload - usually with a binary content.
        """
        url = self._endpoint + '/desktop'
        return self.get(url)
