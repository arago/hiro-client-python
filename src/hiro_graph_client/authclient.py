#!/usr/bin/env python3

from typing import Any, Iterator

from hiro_graph_client.clientlib import HiroApiHandler, AuthenticatedAPI, AbstractTokenHandler


class HiroAuth(AuthenticatedAPI):
    """
    Python implementation for accessing the HIRO Auth REST API.
    See https://core.arago.co/help/specs/?url=definitions/auth.yaml
    """

    def __init__(self,
                 api_handler: HiroApiHandler = None,
                 endpoint: str = None,
                 token_handler: AbstractTokenHandler = None,
                 raise_exceptions: bool = False,
                 proxies: dict = None):
        """
        Constructor

        :param api_handler: Instance of a version handler that contains the current API endpoints.
        :param endpoint: Full url for auth API. Overrides endpoints taken from *api_handler*.
        :param token_handler: External token handler. An internal one is created when this is unset.
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False
        :param proxies: Proxy configuration for *requests*. Default is None.
        """
        super().__init__(api_name='auth',
                         api_handler=api_handler,
                         endpoint=endpoint,
                         token_handler=token_handler,
                         raise_exceptions=raise_exceptions,
                         proxies=proxies)

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
