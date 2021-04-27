import json
import logging
import random
import time
from abc import abstractmethod
from time import sleep

from hiro_graph_client.clientlib import AbstractTokenApiHandler
from websocket import WebSocketApp, ABNF, WebSocketException

logger = logging.getLogger(__name__)
""" The logger for this module """


class AbstractHandledWebSocket:
    """
    The basic class for all WebSockets.
    """
    _ws: WebSocketApp
    _api_handler: AbstractTokenApiHandler
    _proxy_hostname: str
    _proxy_port: str
    _proxy_auth: dict

    _do_exit: bool
    _token_valid: bool
    _reconnect_delay: int

    _protocol: str
    _url: str

    def __init__(self,
                 api_handler: AbstractTokenApiHandler,
                 api_name: str):
        """
        Create the websocket

        :param api_handler: The api handler for authentication.
        :param api_name: The name of the ws api.
        """
        self._url, self._protocol, self._proxy_hostname, self._proxy_port, self._proxy_auth = \
            api_handler.get_websocket_config(api_name)

        self._api_handler = api_handler
        self._token_valid = False
        self._do_exit = False
        self._reconnect_delay = 0

        random.seed(time.time_ns())

    def _check_message(self, ws: WebSocketApp, message: str) -> None:
        """
        Look for error 401. Try to reconnect with a new token when this is encountered.

        :param ws: WebSocketApp
        :param message: Error message as json string
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Received message: " + message)

        message = json.loads(message)
        if isinstance(message, dict):
            error = message.get("error")
            if error:
                code = int(message.get("code"))
                if code == 401:
                    if self._token_valid:
                        self._do_exit = True
                        self._token_valid = False
                        self._api_handler.refresh_token()
                        self._reconnect_delay = 0
                        raise RefreshTokenWebSocketException("Got error 401.")
                    else:
                        self._do_exit = True
                        raise WebSocketException("Got error 401 and token was never valid.")

        self._token_valid = True
        self.on_message(ws, message)

    def _check_open(self, ws: WebSocketApp) -> None:
        """
        Reset *self._reconnect_delay* on open message. Then call *self.on_open*.

        :param ws: WebSocketApp
        """
        logger.debug("Connection to {} open.".format(self._url))

        self._reconnect_delay = 0
        self.on_open(ws)

    def _check_close(self, ws: WebSocketApp, code: int, reason: str):
        """
        Call *self.on_close*. Then, if code is 2000, an intentional shutdown is executed. Try to reconnect otherwise.

        :param ws: WebSocketApp
        :param code: Code of close message
        :param reason: Reason str of close message
        """
        logger.debug("Received close: {} {}.".format(code, reason))

        self.on_close(ws, code, reason)

        if code == 2000:
            raise CloseWebSocketException(reason)
        else:
            self._do_exit = False

    def _check_error(self, ws: WebSocketApp, error: Exception) -> None:
        """
        Filters CloseWebSocketException and RefreshTokenWebSocketException and handles them. All other Exceptions are
        given to *self.on_error*.

        :param ws: WebSocketApp
        :param error: Exception
        """
        if isinstance(error, CloseWebSocketException):
            self._do_exit = True
            logger.debug("Leaving websocket: " + error.args[0])
            return

        if isinstance(error, RefreshTokenWebSocketException):
            self._do_exit = False
            logger.debug("Refreshing token: " + error.args[0])
            return

        logger.error("Received error: {}.".format(error))
        self.on_error(ws, error)

    ###############################################################################################################
    # Public API
    ###############################################################################################################

    @abstractmethod
    def on_open(self, ws: WebSocketApp):
        pass

    @abstractmethod
    def on_close(self, ws: WebSocketApp, code: int, reason: str):
        pass

    @abstractmethod
    def on_message(self, ws: WebSocketApp, message: str):
        pass

    @abstractmethod
    def on_error(self, ws: WebSocketApp, error: Exception):
        pass

    def send(self, message: str):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Sending message: " + message)
        self._ws.send(message)

    def run(self) -> None:
        """
        The run loop. Tries to keep the websocket and reconnects unless *self._do_exit* is True.
        """
        while not self._do_exit:
            header: dict = {
                "Sec-WebSocket-Protocol": "{}, token-{}".format(self._protocol, self._api_handler.token)
            }

            self._ws = WebSocketApp(self._url,
                                    header=header,
                                    on_open=lambda ws: self._check_open(ws),
                                    on_close=lambda ws, code, reason: self._check_close(ws, code, reason),
                                    on_message=lambda ws, msg: self._check_message(ws, msg),
                                    on_error=lambda ws, err: self._check_error(ws, err),
                                    on_ping=lambda ws, data: ws.send(data, opcode=ABNF.OPCODE_PONG))

            self._ws.run_forever(http_proxy_host=self._proxy_hostname,
                                 http_proxy_port=self._proxy_port,
                                 http_proxy_auth=self._proxy_auth)

            if not self._do_exit and self._reconnect_delay:
                sleep(self._reconnect_delay)

                self._reconnect_delay = (self._reconnect_delay + 1) if self._reconnect_delay < 10 \
                    else (self._reconnect_delay + 10) if self._reconnect_delay < 60 \
                    else random.randint(60, 600)

    def close(self) -> None:
        """
        Intentionally closes this websocket by setting status (code) 2000.
        """
        self._ws.close(status=2000, reason="Intentionally closing down")


###################################################################################################################
# Exceptions
###################################################################################################################

class CloseWebSocketException(WebSocketException):
    """
    This exception closes the websocket intentionally.
    """
    pass


class RefreshTokenWebSocketException(WebSocketException):
    """
    This exception is thrown when a token expires
    """
    pass
