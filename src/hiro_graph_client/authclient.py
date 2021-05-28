#!/usr/bin/env python3

from typing import Any, Iterator

from hiro_graph_client.clientlib import AuthenticatedAPIHandler, AbstractTokenApiHandler


class HiroAuth(AuthenticatedAPIHandler):
    """
    Python implementation for accessing the HIRO Auth REST API.
    See https://core.arago.co/help/specs/?url=definitions/auth.yaml
    """

    def __init__(self, api_handler: AbstractTokenApiHandler):
        """
        Constructor

        :param api_handler: External API handler.
        """
        super().__init__(api_name='auth',
                         api_handler=api_handler)

    ###############################################################################################################
    # REST API operations against the auth API
    ###############################################################################################################

    def get_identity(self) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/account'`

        :return: The result payload
        """
        url = self.endpoint + '/me/account'
        return self.get(url)

    def get_avatar(self) -> Iterator[bytes]:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/avatar'`

        :return: The result payload generator over binary data. Complete binary payload is an image/png.
        """
        url = self.endpoint + '/me/avatar'
        yield from self.get_binary(url, accept='image/png')

    def put_avatar(self, data: Any) -> dict:
        """
        HIRO REST query API: `PUT self._auth_endpoint + '/me/avatar'`

        :param data: Binary data for image/png of avatar.
        :return: The result payload
        """
        url = self.endpoint + '/me/avatar'
        return self.put_binary(url, data, content_type='image/png')

    def change_password(self, old_password: str, new_password: str) -> dict:
        """
        HIRO REST query API: `PUT self._auth_endpoint + '/me/password'`

        :param old_password: The old password to replace.
        :param new_password: The new password.
        :return: The result payload
        """
        url = self.endpoint + '/me/password'

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
        url = self.endpoint + '/me/profile'
        return self.get(url)

    def post_profile(self, data: dict) -> dict:
        """
        HIRO REST query API: `POST self._auth_endpoint + '/me/profile`

        :param data: The attributes for the profile.
               See https://core.arago.co/help/specs/?url=definitions/auth.yaml#/[Me]_Identity/post_me_profile
        :return: The result payload
        """
        url = self.endpoint + '/me/profile'
        return self.post(url, data)

    def get_roles(self) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/roles`

        :return: The result payload
        """
        url = self.endpoint + '/me/roles'
        return self.get(url)

    def get_teams(self) -> dict:
        """
        HIRO REST query API: `GET self._auth_endpoint + '/me/teams'`

        :return: The result payload
        """
        url = self.endpoint + '/me/teams'
        return self.get(url)
