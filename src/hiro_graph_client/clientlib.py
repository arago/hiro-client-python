#!/usr/bin/env python3

import json
import threading
import time
from abc import abstractmethod
from typing import Optional, Any, Iterator
from urllib.parse import quote, urlencode

import backoff
import requests
import requests.packages.urllib3.exceptions

BACKOFF_ARGS = [
    backoff.expo,
    requests.exceptions.RequestException
]
BACKOFF_KWARGS = {
    'max_tries': 2,
    'jitter': backoff.random_jitter,
    'giveup': lambda e: e.response is not None and e.response.status_code < 500
}


def accept_all_certs():
    """
    Globally disable InsecureRequestWarning
    """
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


class TokenInfo:
    """
    This class stores token information
    """

    token: str = None
    """ The token string """
    expires_at = -1
    """ Token expiration in ms since epoch"""
    refresh_token: str = None
    """ The refresh token to use - if any."""
    last_update = 0
    """ Timestamp of when the token has been fetched in ms."""

    def __init__(self, token: str = None, refresh_token: str = None, expires_at: int = -1):
        """
        Constructor

        :param token: The token string
        :param refresh_token: A refresh token
        :param expires_at: Token expiration in ms since epoch
        """
        self.token = token
        self.expires_at = expires_at
        self.refresh_token = refresh_token
        self.last_update = self.get_epoch_millis() if token else 0

    @staticmethod
    def get_epoch_millis() -> int:
        """
        Get timestamp
        :return: Current epoch in milliseconds
        """
        return int(round(time.time() * 1000))

    def parse_token_result(self, res: dict, what: str) -> None:
        """
        Parse the result payload and extract token information.

        :param res: The result payload from the backend.
        :param what: What token command has been issued (for error messages).
        :raises AuthenticationTokenError: When the token request returned an error.
        """
        if 'error' in res:
            message: str = '{}: {}'.format(what, res['error'].get('message'))
            code: int = int(res['error'].get('code'))

            if code == 401:
                raise TokenExpiredError(message, code)
            else:
                raise AuthenticationTokenError(message, code)

        self.token = res.get('_TOKEN')

        expires_at = res.get('expires-at')
        if expires_at:
            self.expires_at = int(expires_at)
        else:
            expires_in = res.get('expires_in')
            if expires_in:
                self.expires_at = self.get_epoch_millis() + int(expires_in) * 1000

        refresh_token = res.get('refresh_token')
        if refresh_token:
            self.refresh_token = refresh_token

        self.last_update = self.get_epoch_millis()

    def expired(self) -> bool:
        """
        Check token expiration

        :return: True when the token has been expired (expires_at <= get_epoch_mills())
        """
        return self.expires_at <= self.get_epoch_millis()

    def fresh(self, span: int = 30000) -> bool:
        """
        Check, whether the last token fetched is younger than span ms.

        :param span: Timespan in ms in which a token is considered fresh. Default is 30 sec (30000ms).
        :return: True when the last update was less than span ms.
        """

        return (self.get_epoch_millis() - self.last_update) < span


class APIConfig:
    def __init__(self,
                 username: str,
                 password: str,
                 client_id: str,
                 client_secret: str,
                 endpoint: str,
                 auth_endpoint: str,
                 raise_exceptions: bool = False,
                 proxies: dict = None):
        """
        Constructor

        :param username: Username for authentication
        :param password: Password for authentication
        :param client_id: OAuth client_id for authentication
        :param client_secret: OAuth client_secret for authentication
        :param endpoint: Full url for service API
        :param auth_endpoint: Full url for auth
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False.
        :param proxies: Proxy configuration for *requests*. Default is None.
        """
        self._username = username
        self._password = password
        self._client_id = client_id
        self._client_secret = client_secret
        self._endpoint = endpoint
        self._auth_endpoint = auth_endpoint
        self._proxies = proxies
        self._raise_exceptions = raise_exceptions


class AbstractAPI(APIConfig):
    def __init__(self,
                 username: str,
                 password: str,
                 client_id: str,
                 client_secret: str,
                 endpoint: str,
                 auth_endpoint: str,
                 raise_exceptions: bool = False,
                 proxies: dict = None):
        """
        Constructor

        :param username: Username for authentication
        :param password: Password for authentication
        :param client_id: OAuth client_id for authentication
        :param client_secret: OAuth client_secret for authentication
        :param endpoint: Full url for service API
        :param auth_endpoint: Full url for auth
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False.
        :param proxies: Proxy configuration for *requests*. Default is None.
        """

        super().__init__(username,
                         password,
                         client_id,
                         client_secret,
                         endpoint,
                         auth_endpoint,
                         raise_exceptions,
                         proxies)

        self._headers = {'Content-type': 'application/json',
                         'Accept': 'text/plain, application/json'
                         }

    @classmethod
    def new_from(cls, other: APIConfig):
        return cls(other._username,
                   other._password,
                   other._client_id,
                   other._client_secret,
                   other._endpoint,
                   other._auth_endpoint,
                   other._raise_exceptions,
                   other._proxies)

    ###############################################################################################################
    # Basic requests
    ###############################################################################################################

    @backoff.on_exception(*BACKOFF_ARGS, **BACKOFF_KWARGS)
    def get_binary(self, url: str, accept: str = None, token: str = None) -> Iterator[bytes]:
        """
        Implementation of GET for binary data.

        :param url: Url to use
        :param accept: Mimetype for accept. Will be set to */* if not given.
        :param token: External token to use. Default is False to handle token internally.
        :return: Yields an iterator over raw chunks of the response payload.
        """
        headers = self._get_headers(token, content=False)
        headers['Accept'] = accept or "*/*"
        with requests.get(url,
                          headers=headers,
                          verify=False,
                          stream=True,
                          proxies=self._get_proxies()) as res:
            self._check_response(res, token)

            yield from res.iter_content(chunk_size=65536)

    @backoff.on_exception(*BACKOFF_ARGS, **BACKOFF_KWARGS)
    def post_binary(self, url: str, data: Any, content_type: str = None, token: str = None) -> dict:
        """
        Implementation of POST for binary data.

        :param url: Url to use
        :param data: The payload to POST. This can be anything 'requests.post(data=...)' supports.
        :param content_type: The content type of the data. Defaults to "application/octet-stream" internally if unset.
        :param token: External token to use. Default is False to handle token internally.
        :return: The payload of the response
        """
        headers = self._get_headers(token)
        headers['Content-Type'] = content_type or "application/octet-stream"
        res = requests.post(url,
                            data=data,
                            headers=headers,
                            verify=False,
                            proxies=self._get_proxies())
        return self._parse_json_response(res, token)

    @backoff.on_exception(*BACKOFF_ARGS, **BACKOFF_KWARGS)
    def put_binary(self, url: str, data: Any, content_type: str = None, token: str = None) -> dict:
        """
        Implementation of PUT for binary data.

        :param url: Url to use
        :param data: The payload to PUT. This can be anything 'requests.put(data=...)' supports.
        :param content_type: The content type of the data. Defaults to "application/octet-stream" internally if unset.
        :param token: External token to use. Default is False to handle token internally.
        :return: The payload of the response
        """
        headers = self._get_headers(token)
        headers['Content-Type'] = content_type or "application/octet-stream"
        res = requests.put(url,
                           data=data,
                           headers=headers,
                           verify=False,
                           proxies=self._get_proxies())
        return self._parse_json_response(res, token)

    @backoff.on_exception(*BACKOFF_ARGS, **BACKOFF_KWARGS)
    def get(self, url: str, token: str = None) -> dict:
        """
        Implementation of GET

        :param url: Url to use
        :param token: External token to use. Default is False to handle token internally.
        :return: The payload of the response
        """
        res = requests.get(url,
                           headers=self._get_headers(token, content=False),
                           verify=False,
                           proxies=self._get_proxies())
        return self._parse_json_response(res, token)

    @backoff.on_exception(*BACKOFF_ARGS, **BACKOFF_KWARGS)
    def post(self, url: str, data: Any, token: str = None) -> dict:
        """
        Implementation of POST

        :param url: Url to use
        :param data: The payload to POST
        :param token: External token to use. Default is False to handle token internally.
        :return: The payload of the response
        """
        res = requests.post(url,
                            json=data,
                            headers=self._get_headers(token, content=True),
                            verify=False,
                            proxies=self._get_proxies())
        return self._parse_json_response(res, token)

    @backoff.on_exception(*BACKOFF_ARGS, **BACKOFF_KWARGS)
    def put(self, url: str, data: Any, token: str = None) -> dict:
        """
        Implementation of PUT

        :param url: Url to use
        :param data: The payload to PUT
        :param token: External token to use. Default is False to handle token internally.
        :return: The payload of the response
        """
        res = requests.put(url,
                           json=data,
                           headers=self._get_headers(token, content=True),
                           verify=False,
                           proxies=self._get_proxies())
        return self._parse_json_response(res, token)

    @backoff.on_exception(*BACKOFF_ARGS, **BACKOFF_KWARGS)
    def delete(self, url: str, token: str = None) -> dict:
        """
        Implementation of DELETE

        :param url: Url to use
        :param token: External token to use. Default is False to handle token internally.
        :return: The payload of the response
        """
        res = requests.delete(url,
                              headers=self._get_headers(token, content=False),
                              verify=False,
                              proxies=self._get_proxies())
        return self._parse_json_response(res, token)

    ###############################################################################################################
    # Tool methods for requests
    ###############################################################################################################

    def _get_proxies(self) -> dict:
        """
        Create a copy of proxies if they exists or return None

        :return: copy of self._proxies or None
        """
        return self._proxies.copy() if self._proxies else None

    def _get_headers(self, token: str, content: bool = True) -> dict:
        """
        Create a header dict for requests. Uses abstract method *self._handle_token()*.

        :param token: An external token that gets passed through if it is not None.
        :param content: Remove 'Content-Type' from headers when set to False.
        :return: A dict containing header values for requests.
        """
        token = self._handle_token(token)
        headers = self._headers.copy()

        if not content and 'Content-Type' in headers:
            del headers['Content-Type']

        if token:
            headers['Authorization'] = "Bearer " + token

        return headers

    @staticmethod
    def _get_query_part(params: dict) -> str:
        """
        Create the query part of an url. Keys in *params* that are set to None are removed.

        :param params: A dict of params to use for the query.
        :return: The query part of an url with a leading '?', or an empty string when query is empty.
        """
        params_cleaned = {k: v for k, v in params.items() if v is not None}
        return '?' + urlencode(params_cleaned, quote_via=quote, safe="/,") if params_cleaned else ""

    def _parse_json_response(self, res: requests.Response, token: str = None) -> dict:
        """
        Parse the response of the backend.

        :param res: The result payload
        :param token: The external token if provided
        :return: The result payload
        :raises RequestException: On HTTP errors.
        """
        try:
            self._check_response(res, token)
            self._check_status_error(res)
            return res.json()
        except (json.JSONDecodeError, ValueError):
            return {"error": {"message": res.text, "code": 999}}

    def _check_status_error(self, res: requests.Response) -> None:
        """
        Catch exceptions and rethrow them with additional information returned by the error response body.

        :param res: The response
        :raises requests.exceptions.HTTPError: When an HTTPError occurred.
        """
        try:
            if self._raise_exceptions:
                res.raise_for_status()
                if res.status_code > 600:
                    raise requests.exceptions.HTTPError(
                        u'%s Illegal return code: %s for url: %s' % (res.status_code, res.reason, res.url),
                        response=res)

        except requests.exceptions.HTTPError as err:
            http_error_msg = str(err.args[0])

            if res.content:
                try:
                    json_result: dict = res.json()
                    message = json_result['error']['message']
                    http_error_msg += ": " + message
                except (json.JSONDecodeError, KeyError):
                    if '_TOKEN' not in res.text:
                        http_error_msg += ": " + str(res.text)

            raise requests.exceptions.HTTPError(http_error_msg, response=err.response) from err

    ###############################################################################################################
    # Response and token handling
    # Abstract methods
    ###############################################################################################################

    @abstractmethod
    def _check_response(self, res: requests.Response, token: str) -> None:
        """
        Abstract base function for response checking. Might check for authentication errors depending on the context.

        :param res: The result payload
        :param token: The external token if provided
        """
        raise RuntimeError('Cannot use _check_response of this abstract class.')

    @abstractmethod
    def _handle_token(self, token: str) -> Optional[str]:
        """
        Abstract base function for token handling.

        :param token: An external token.
        :return: A valid token that might have been fetched automatically depending on the context.
        """
        raise RuntimeError('Cannot use _handle_token of this abstract class.')


class TokenHandler(AbstractAPI):
    """
    API Tokens will be fetched using this class. It does not handle any automatic token fetching, refresh or token
    expiry. This has to be checked and triggered by the *caller*.

    The methods of this class are thread-safe so it can be shared between several HIRO objects.

    It is built this way to avoid endless calling loops when resolving tokens.
    """

    _token_info: TokenInfo = None
    """Contains all token information"""

    _lock: threading.RLock = None
    """Reentrant mutex for thread safety"""

    def __init__(self,
                 username: str,
                 password: str,
                 client_id: str,
                 client_secret: str,
                 endpoint: str,
                 auth_endpoint: str,
                 raise_exceptions: bool = False,
                 proxies: dict = None):
        """
        Constructor

        :param username: Username for authentication
        :param password: Password for authentication
        :param client_id: OAuth client_id for authentication
        :param client_secret: OAuth client_secret for authentication
        :param endpoint: Full url for service API
        :param auth_endpoint: Full url for auth
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False.
        :param proxies: Proxy configuration for *requests*. Default is None.
        """
        super().__init__(username,
                         password,
                         client_id,
                         client_secret,
                         endpoint,
                         auth_endpoint,
                         raise_exceptions,
                         proxies)

        self._token_info = TokenInfo()
        self._lock = threading.RLock()

    @property
    def token(self):
        with self._lock:
            if not self._token_info.token:
                self.get_token()
            elif self._token_info.expired():
                self.refresh_token()

            return self._token_info.token

    def get_token(self) -> None:
        """
        Construct a request to obtain a new token. API self._auth_endpoint + '/app'

        :raises AuthenticationTokenError: When no auth_endpoint is set.
        """
        with self._lock:
            if not self._auth_endpoint:
                raise AuthenticationTokenError(
                    'Token is invalid and auth_endpoint for obtaining is not set.')

            url = self._auth_endpoint + '/app'
            data = {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "username": self._username,
                "password": self._password
            }

            res = self.post(url, data)
            self._token_info.parse_token_result(res, 'Get token')

    def refresh_token(self) -> None:
        """
        Construct a request to refresh an existing token. API self._auth_endpoint + '/refresh'.
        Does not refresh tokens that are younger than 30 sec to avoid refresh storms on parallel connections.

        :raises AuthenticationTokenError: When no auth_endpoint is set.
        """
        with self._lock:
            if not self._auth_endpoint:
                raise AuthenticationTokenError(
                    'Token is invalid and auth_endpoint for refresh is not set.')

            if self._token_info.fresh():
                return

            if not self._token_info.refresh_token:
                self.get_token()
                return

            url = self._auth_endpoint + '/refresh'
            data = {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "refresh_token": self._token_info.refresh_token
            }

            try:
                res = self.post(url, data)
                self._token_info.parse_token_result(res, 'Refresh token')
            except TokenExpiredError:
                self.get_token()

    ###############################################################################################################
    # Response and token handling
    ###############################################################################################################

    def _check_response(self, res: requests.Response, token: str) -> None:
        """
        This is a dummy method. No response checking here.

        :param res: The result payload
        :param token: The external token if provided
        """
        return

    def _handle_token(self, token: str) -> Optional[str]:
        """
        Just return *token*. This *token* is usually None in this context, therefore a header without Authorization
        will be created in *self._get_headers()*.

        Does *not* try to obtain or refresh a token.

        :param token: An external token that gets passed through - usually None in this context here.
        :return: *token* given.
        """
        return token


class AuthenticatedAPI(AbstractAPI):
    """
    Python implementation for accessing a REST API with authentication.
    """

    _token_handler: TokenHandler = None

    def __init__(self,
                 username: str,
                 password: str,
                 client_id: str,
                 client_secret: str,
                 endpoint: str,
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
        :param endpoint: Full url for IAM API
        :param auth_endpoint: Full url for auth
        :param raise_exceptions: Raise exceptions on HTTP status codes that denote an error. Default is False
        :param proxies: Proxy configuration for *requests*. Default is None.
        :param token_handler: External token handler. An internal one is created when this is unset.
        """
        super().__init__(username,
                         password,
                         client_id,
                         client_secret,
                         endpoint,
                         auth_endpoint,
                         raise_exceptions,
                         proxies)

        self._token_handler = token_handler or TokenHandler.new_from(self)

    @classmethod
    def new_from(cls, other: APIConfig, token_handler: TokenHandler = None):
        return cls(other._username,
                   other._password,
                   other._client_id,
                   other._client_secret,
                   other._endpoint,
                   other._auth_endpoint,
                   other._raise_exceptions,
                   other._proxies,
                   token_handler)

    ###############################################################################################################
    # Response and token handling
    ###############################################################################################################

    def _check_response(self, res: requests.Response, token: str) -> None:
        """
        Response checking. Tries to refresh the token on status_code 401, then raises RequestException to try
        again using backoff.

        :param res: The result payload
        :param token: The external token if provided
        :raises requests.exceptions.RequestException: When an error 401 occurred and the token has been refreshed.
        :raises AuthenticationTokenError: When an external token has been provided but code 401 has been returned
                                          from the backend.
        """
        if res.status_code == 401:
            if token:
                raise AuthenticationTokenError(
                    'Cannot refresh invalid token that was given externally.')

            self._token_handler.refresh_token()

            # Raise this exception to trigger retry with backoff
            raise requests.exceptions.RequestException

    def _handle_token(self, token: str) -> Optional[str]:
        """
        Try to return a valid token by passing it, or obtaining or refreshing it.

        :param token: An external token that gets passed through if it is not None.
        :return: A valid token.
        """
        return token or self._token_handler.token


class AuthenticationTokenError(Exception):
    """
    Class for unrecoverable failures with access tokens.
    Contains a message and an optional message code. If the code is None, no code will be printed in __str__().
    """
    message: str
    code: int

    def __init__(self, message: str, code: int = None):
        self.message = message
        self.code = code

    def __str__(self):
        if self.code is None:
            return "{}: {}".format(self.__class__.__name__, self.message)
        else:
            return "{}: {} ({})".format(self.__class__.__name__, self.message, self.code)


class TokenExpiredError(AuthenticationTokenError):
    """
    Child of *AuthenticationTokenErrors*. Used when tokens expire.
    """
    pass
