import json
import logging
import random
import ssl
import threading
import time
from abc import abstractmethod
from time import sleep

from websocket import WebSocketApp, ABNF, WebSocketException, setdefaulttimeout

from hiro_graph_client.clientlib import AbstractTokenApiHandler

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

    _timeout: int

    _reader_thread: threading.Thread
    _reader_thread_lock: threading.RLock

    _sender_thread_lock: threading.RLock

    MAX_RETRIES = 3

    def __init__(self,
                 api_handler: AbstractTokenApiHandler,
                 api_name: str,
                 timeout: int = 5):
        """
        Create the websocket

        :param api_handler: The api handler for authentication.
        :param api_name: The name of the ws api.
        :param timeout: The timeout for websocket messages. Default is 5sec.
        """
        self._url, self._protocol, self._proxy_hostname, self._proxy_port, self._proxy_auth = \
            api_handler.get_websocket_config(api_name)

        self._api_handler = api_handler

        self._timeout = timeout

        self._reader_thread = threading.Thread(target=AbstractHandledWebSocket._run, args=(self,))
        self._reader_thread_lock = threading.RLock()

        self._sender_thread_lock = threading.RLock()

        setdefaulttimeout(timeout)

        random.seed(time.time_ns())

    def _check_message(self, ws: WebSocketApp, message: str) -> None:
        """
        Look for error 401. Try to reconnect with a new token when this is encountered.

        :param ws: WebSocketApp
        :param message: Error message as json string
        :raise ReconnectWebSocketException: When a token is no longer valid on error code 401.
        :raise WebSocketException: When error 401 is received and the token was never valid.
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Received message: " + message)

        json_message = json.loads(message)
        if isinstance(json_message, dict):
            error = json_message.get("error")
            if error:
                code = int(error.get("code"))
                message = str(error.get("message"))
                if code == 401:
                    # Always set _do_exit on 401. It will be handled again in self._check_error if no other Exception
                    # occurs.
                    self._do_exit = True
                    if self._token_valid:
                        self._api_handler.refresh_token()

                        # Reset values for reconnect
                        self._reconnect_delay = 0
                        self._do_exit = False

                        raise ReconnectWebSocketException(
                            "Refreshing token because of error {} \"{}\"".format(code, message))
                    else:
                        raise WebSocketException(
                            "Token was never valid and received error {} \"{}\"".format(code, message))

        self._token_valid = True
        self._reconnect_delay = 0
        self.on_message(ws, message)

    def _check_open(self, ws: WebSocketApp) -> None:
        """
        Call *self.on_open* and set *self._do_exit* to False if opening succeeded.

        :param ws: WebSocketApp
        """
        logger.debug("Connection to {} open.".format(self._url))

        self.on_open(ws)

        self._do_exit = False

    def _check_close(self, ws: WebSocketApp, code: int, reason: str):
        """
        Call *self.on_close*. When *code* and *reason* are None, the close has been issued locally and not by the
        remote side.

        :param ws: WebSocketApp
        :param code: Code of close message
        :param reason: Reason str of close message
        """
        if code or reason:
            logger.debug("Received close from remote: {} {}.".format(code, reason))
        else:
            logger.debug("Received local close.")

        self.on_close(ws, code, reason)

    def _check_error(self, ws: WebSocketApp, error: Exception) -> None:
        """
        Just log the error and propagate it to *self.on_error*.

        :param ws: WebSocketApp
        :param error: Exception
        """
        logger.error("Received error: {}.".format(error))
        self.on_error(ws, error)

    def _run(self) -> None:
        """
        The _run loop. Tries to keep the websocket and reconnects unless *self._do_exit* is True.
        """
        self._reconnect_delay = 0
        self._do_exit = False

        while not self._do_exit:
            self._reconnect_delay = self._backoff(self._reconnect_delay)

            # This value get set to False in *self._check_open* when open succeeds.
            self._do_exit = True
            self._token_valid = False

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
                                 http_proxy_auth=self._proxy_auth,
                                 sslopt={
                                     "cert_reqs": ssl.CERT_NONE
                                 } if AbstractTokenApiHandler.accept_all_certs else None)

    @staticmethod
    def _backoff(reconnect_delay: int) -> int:
        """
        Sleeps for *reconnect_delay* seconds, then returns the delay in seconds for the next try.

        :param reconnect_delay: Delay in seconds to wait.
        :return: Next value for the delay.
        """
        if reconnect_delay:
            sleep(reconnect_delay)

        return (reconnect_delay + 1) if reconnect_delay < 10 \
            else (reconnect_delay + 10) if reconnect_delay < 60 \
            else random.randint(60, 600)

    ###############################################################################################################
    # Public API Reader thread
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

    ###############################################################################################################
    # Public API Main Writer thread
    ###############################################################################################################

    def start_reader(self) -> None:
        """
        Start the background thread for receiving messages from the websocket.
        """
        with self._reader_thread_lock:
            self._reader_thread.start()

    def join_reader(self, timeout: int = None) -> None:
        """
        :param timeout: Optional timeout in seconds for joining the reader thread.
        """
        with self._reader_thread_lock:
            self._reader_thread.join(timeout=timeout)

    def close(self, timeout: int = None) -> None:
        """
        Intentionally closes this websocket by setting status (code) 2000. Joins on the reader before returning.

        :param timeout: Optional timeout in seconds for joining the reader thread.
        """
        self._do_exit = True
        self._ws.close(status=ABNF.OPCODE_CLOSE, reason="{} closing down".format(self._api_handler.get_user_agent()))
        self.join_reader(timeout)

    def send(self, message: str) -> None:
        """
        Send message across the websocket. Make sure, that this is thread-saf.

        :param message: Message as string
        :raise WebSocketException: If a message cannot be sent and all retries have been exhausted.
        """
        with self._sender_thread_lock:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Sending message: " + message)

            retries = 0
            retry_delay = 0

            while True:
                retry_delay = self._backoff(retry_delay)

                try:
                    self._ws.send(message)
                    return
                except Exception as err:
                    if retries >= self.MAX_RETRIES:
                        raise WebSocketException from err

                    logger.warn('Retrying to send message because of error "%s"', str(err))
                    retries += 1


###################################################################################################################
# Exceptions
###################################################################################################################

class CloseWebSocketException(WebSocketException):
    """
    This exception closes the websocket intentionally.
    """
    pass


class ReconnectWebSocketException(WebSocketException):
    """
    This exception reconnects the websocket intentionally.
    """
    pass
