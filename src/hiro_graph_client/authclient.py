#!/usr/bin/env python3

from typing import Any, Iterator

from hiro_graph_client.clientlib import AuthenticatedAPI, AbstractTokenHandler


class HiroAuth(AuthenticatedAPI):
    """
    Python implementation for accessing the HIRO App REST API.
    See https://core.arago.co/help/specs/?url=definitions/app.yaml
    """

    def __init__(self,
                 endpoint: str,
                 token_handler: AbstractTokenHandler,
                 raise_exceptions: bool = False,
                 proxies: dict = None):
        """
        Constructor

        :param endpoint: Full url for Auth API
        :param token_handler: External token handler. An internal one is created when this is unset.
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False
        :param proxies: Proxy configuration for *requests*. Default is None.
        """
        super().__init__(endpoint,
                         raise_exceptions,
                         proxies,
                         token_handler)

    ###############################################################################################################
    # REST API operations against the auth API
    ###############################################################################################################

    def get_identity(self) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/account'`

        :return: The result payload
        """
        url = self._endpoint + '/me/account'
        return self.get(url)

    def get_avatar(self) -> Iterator[bytes]:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/avatar'`

        :return: The result payload yields over binary data. Complete binary payload is an image/png.
        """
        url = self._endpoint + '/me/avatar'
        yield self.get_binary(url, accept='image/png')

    def put_avatar(self, data: Any) -> dict:
        """
        HIRO REST query API: `PUT self._auth_endpoint + '/me/avatar'`

        :param data: Binary data for image/png of avatar.
        :return: The result payload
        """
        url = self._endpoint + '/me/avatar'
        return self.put_binary(url, data, content_type='image/png')

    def change_password(self, old_password: str, new_password: str) -> dict:
        """
        HIRO REST query API: `PUT self._auth_endpoint + '/me/password'`

        :param old_password: The old password to replace.
        :param new_password: The new password.
        :return: The result payload
        """
        url = self._endpoint + '/me/password'

        data = {
            "oldPassword": old_password,
            "newPassword": new_password
        }

        return self.put(url, data)

    def get_profile(self) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/profile`

        :return: The result payload
        """
        url = self._endpoint + '/me/profile'
        return self.get(url)

    def post_profile(self, data: dict) -> dict:
        """
        HIRO REST query API: `POST self._auth_endpoint + '/me/profile`

        :param data: The attributes for the profile.
               See https://core.arago.co/help/specs/?url=definitions/auth.yaml#/[Me]_Identity/post_me_profile
        :return: The result payload
        """
        url = self._endpoint + '/me/profile'
        return self.post(url, data)

    def get_roles(self) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/roles`

        :return: The result payload
        """
        url = self._endpoint + '/me/roles'
        return self.get(url)

    def get_teams(self) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/teams'`

        :return: The result payload
        """
        url = self._endpoint + '/me/teams'
        return self.get(url)
