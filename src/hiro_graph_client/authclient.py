#!/usr/bin/env python3

from typing import Any, Iterator

from hiro_graph_client.clientlib import AuthenticatedAPI, TokenHandler


class HiroAuth(AuthenticatedAPI):
    """
    Python implementation for accessing the HIRO App REST API.
    See https://core.arago.co/help/specs/?url=definitions/app.yaml
    """

    def __init__(self,
                 username: str,
                 password: str,
                 client_id: str,
                 client_secret: str,
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
        :param auth_endpoint: Full url for Auth API
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False
        :param proxies: Proxy configuration for *requests*. Default is None.
        :param token_handler: External token handler. An internal one is created when this is unset.
        """
        super().__init__(username,
                         password,
                         client_id,
                         client_secret,
                         auth_endpoint,
                         auth_endpoint,
                         raise_exceptions,
                         proxies,
                         token_handler)

    ###############################################################################################################
    # REST API operations against the auth API
    ###############################################################################################################

    def get_identity(self, token: str = None) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/account'`

        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/me/account'
        return self.get(url, token)

    def get_avatar(self, token: str = None) -> Iterator[bytes]:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/avatar'`

        :param token: Optional external token.
        :return: The result payload as Iterator over binary data. Complete binary payload is an image/png.
        """
        url = self._endpoint + '/me/avatar'
        return self.get_binary(url, token)

    def put_avatar(self, data: Any, token: str = None) -> dict:
        """
        HIRO REST query API: `PUT self._auth_endpoint + '/me/avatar'`

        :param data: Binary data for image/png of avatar.
        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/me/avatar'
        return self.put_binary(url, data, 'image/png', token)

    def change_password(self, old_password: str, new_password: str, token: str = None) -> dict:
        """
        HIRO REST query API: `PUT self._auth_endpoint + '/me/password'`

        :param old_password: The old password to replace.
        :param new_password: The new password.
        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/me/password'

        data = {
            "oldPassword": old_password,
            "newPassword": new_password
        }

        return self.put(url, data, token)

    def get_profile(self, token: str = None) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/profile`

        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/me/profile'
        return self.get(url, token)

    def post_profile(self, data: dict, token: str = None) -> dict:
        """
        HIRO REST query API: `POST self._auth_endpoint + '/me/profile`

        :param data: The attributes for the profile.
               See https://core.arago.co/help/specs/?url=definitions/auth.yaml#/[Me]_Identity/post_me_profile
        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/me/profile'
        return self.post(url, data, token)

    def get_roles(self, token: str = None) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/roles`

        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/me/roles'
        return self.get(url, token)

    def get_teams(self, token: str = None) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/teams'`

        :param token: Optional external token.
        :return: The result payload
        """
        url = self._endpoint + '/me/teams'
        return self.get(url, token)
