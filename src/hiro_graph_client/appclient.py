#!/usr/bin/env python3

from typing import Iterator
from urllib.parse import quote_plus

from hiro_graph_client.clientlib import AuthenticatedAPI, TokenHandler


class HiroApp(AuthenticatedAPI):
    """
    Python implementation for accessing the HIRO App REST API.
    See https://core.arago.co/help/specs/?url=definitions/app.yaml
    """

    def __init__(self,
                 username: str,
                 password: str,
                 client_id: str,
                 client_secret: str,
                 app_endpoint: str,
                 auth_endpoint: str,
                 raise_exceptions: bool = False,
                 proxies: dict = None,
                 token_handler: TokenHandler = None):
        """
        Constructor

        :param username: Username for authentication
        :param password: Password for authentication
        :param client_id: OAuth client_id for authentication
        :param client_secret: OAuth client_secret for authentication
        :param app_endpoint: Full url for App API
        :param auth_endpoint: Full url for auth
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False
        :param proxies: Proxy configuration for *requests*. Default is None.
        :param token_handler: External token handler. An internal one is created when this is unset.
        """
        super().__init__(username,
                         password,
                         client_id,
                         client_secret,
                         app_endpoint,
                         auth_endpoint,
                         raise_exceptions,
                         proxies,
                         token_handler)

    ###############################################################################################################
    # REST API operations
    ###############################################################################################################

    def get_app(self, node_id, token: str = None) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}'`

        :param node_id: ogit/_id of the node/vertex or edge.
        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/' + quote_plus(node_id)
        return self.get(url, token)

    def get_config(self, token: str = None) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/config'`. The token (internal or external) defines the config
        returned.

        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/config'
        return self.get(url, token)

    def get_content(self, node_id, path, token: str = None) -> Iterator[bytes]:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}/content/{path}'`. Get the content of an application.

        :param node_id: ogit/_id of the node/vertex or edge.
        :param path: filename / path of the desired content.
        :param token: Optional external token.
        :return: The result payload as iterator over binary data.
        """
        url = self._endpoint + '/' + quote_plus(node_id) + '/content/' + quote_plus(path)
        return self.get_binary(url, token)

    def get_manifest(self, node_id, token: str = None) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}/manifest'`. Get the manifest of an application.

        :param node_id: ogit/_id of the node/vertex or edge.
        :param token: Optional external token.
        :return: The result payload - usually with a binary content.
        """
        url = self._endpoint + '/' + quote_plus(node_id) + '/manifest'
        return self.get(url, token)

    def get_desktop(self, token: str = None) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/desktop'`. List desktop applications.

        :param token: Optional external token.
        :return: The result payload - usually with a binary content.
        """
        url = self._endpoint + '/desktop'
        return self.get(url, token)
