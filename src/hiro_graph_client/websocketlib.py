import concurrent.futures
import json
import logging
import random
import ssl
import threading
import time
from abc import abstractmethod
from time import sleep
from typing import Optional

from websocket import WebSocketApp, ABNF, WebSocketException, setdefaulttimeout

from hiro_graph_client.clientlib import AbstractTokenApiHandler

logger = logging.getLogger(__name__)
""" The logger for this module """


class AbstractAuthenticatedWebSocketHandler:
    """
    The basic class for all WebSockets.
    """
    _api_handler: AbstractTokenApiHandler
    _proxy_hostname: str
    _proxy_port: str
    _proxy_auth: dict

    _token_valid: bool
    _reconnect_delay: int

    _protocol: str
    _url: str

    _timeout: int
    _auto_reconnect: bool

    _ws: Optional[WebSocketApp]
    _reader_executor: concurrent.futures.ThreadPoolExecutor
    _reader_websocket_condition: threading.Condition
    """ Protects *self._ws* """
    _reader_future: Optional[concurrent.futures.Future]
    _quit_reader: bool

    _inner_exception: Optional[Exception]
    """
    The WebSocketApp catches all exceptions that are thrown in the om_... methods, so we have to store the exceptions
    here.
    """

    _sender_thread_lock: threading.RLock

    MAX_RETRIES = 3

    def __init__(self,
                 api_handler: AbstractTokenApiHandler,
                 api_name: str,
                 timeout: int = 5,
                 auto_reconnect: bool = True):
        """
        Create the websocket

        :param api_handler: The api handler for authentication.
        :param api_name: The name of the ws api.
        :param timeout: The timeout for websocket messages. Default is 5sec.
        :param auto_reconnect: Try to create a new websocket automatically when *self.send()* fails. If this is set
                               to False, a WebSocketException will be raised instead. The default is True.
        """
        self._url, self._protocol, self._proxy_hostname, self._proxy_port, self._proxy_auth = \
            api_handler.get_websocket_config(api_name)

        self._api_handler = api_handler

        self._timeout = timeout
        self._auto_reconnect = auto_reconnect

        self._reader_websocket_condition = threading.Condition()
        self._reader_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._reader_future = None
        self._ws = None
        self._inner_exception = None

        self._sender_thread_lock = threading.RLock()

        setdefaulttimeout(timeout)

        random.seed(time.time_ns())

    def __enter__(self) -> None:
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop(self._timeout)

    def _check_message(self, ws: WebSocketApp, message: str) -> None:
        """
        Look for error 401. Try to reconnect with a new token when this is encountered.
        Sets ReconnectWebSocketException: When a token is no longer valid on error code 401.
        Sets WebSocketException: When error 401 is received and the token was never valid.

        :param ws: WebSocketApp
        :param message: Error message as json string
        """
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Received message: " + message)

        try:
            json_message = json.loads(message)
            if isinstance(json_message, dict):
                error = json_message.get("error")
                if error:
                    code = int(error.get("code"))
                    message = str(error.get("message"))
                    if code == 401:
                        self._quit_reader = True
                        if self._token_valid:
                            self._api_handler.refresh_token()

                            # If we get here, the token has been refreshed successfully.
                            self._reconnect_delay = 0
                            self._quit_reader = False

                            raise ReconnectWebSocketException(
                                "Refreshing token because of error {} \"{}\"".format(code, message))
                        else:
                            raise WebSocketException(
                                "Token was never valid and received error {} \"{}\"".format(code, message))

            # If no error message came in, the token must be valid.
            self._token_valid = True
            self._reconnect_delay = 0

            self.on_message(ws, message)
        except Exception as err:
            self._inner_exception = err
            self._close()
            raise self._inner_exception

    def _check_open(self, ws: WebSocketApp) -> None:
        """
        Call *self.on_open* and set *self._do_exit* to False if opening succeeded.

        :param ws: WebSocketApp
        """
        logger.debug("Connection to {} start.".format(self._url))

        try:
            self.on_open(ws)
            self._quit_reader = False
        except Exception as err:
            self._inner_exception = err
            self._close()
            raise self._inner_exception

    def _check_close(self, ws: WebSocketApp, code: int, reason: str):
        """
        Call *self.on_close*. When *code* and *reason* are None, the stop has been issued locally and not by the
        remote side.

        :param ws: WebSocketApp
        :param code: Code of stop message
        :param reason: Reason str of stop message
        """
        if code or reason:
            logger.debug("Received stop from remote: {} {}.".format(code, reason))
        else:
            logger.debug("Received local stop.")

        self.on_close(ws, code, reason)

    def _check_error(self, ws: WebSocketApp, error: Exception) -> None:
        """
        Just log the error and propagate it to *self.on_error*.

        :param ws: WebSocketApp
        :param error: Exception
        """
        logger.error("Received error: {}.".format(error))

        try:
            self.on_error(ws, error)
        except Exception as err:
            self._inner_exception = err
            self._close()
            raise self._inner_exception

    def _run(self) -> None:
        """
        The _run loop. Tries to keep the websocket and reconnects unless *self._do_exit* is True.

        :raise Exception: The stored *self._inner_exception* will be raised on exit if it exists.
        """
        self._reconnect_delay = 0
        self._quit_reader = False

        while not self._quit_reader:
            self._reconnect_delay = self._backoff(self._reconnect_delay)

            # This value get set to False in *self._check_open* when start succeeds.
            self._quit_reader = True
            self._token_valid = False
            self._inner_exception = None

            header: dict = {
                "Sec-WebSocket-Protocol": "{}, token-{}".format(self._protocol, self._api_handler.token)
            }

            with self._reader_websocket_condition:
                self._ws = WebSocketApp(self._url,
                                        header=header,
                                        on_open=lambda ws: self._check_open(ws),
                                        on_close=lambda ws, code, reason: self._check_close(ws, code, reason),
                                        on_message=lambda ws, msg: self._check_message(ws, msg),
                                        on_error=lambda ws, err: self._check_error(ws, err),
                                        on_ping=lambda ws, data: ws.send(data, opcode=ABNF.OPCODE_PONG))

                self._reader_websocket_condition.notify_all()

            self._ws.run_forever(http_proxy_host=self._proxy_hostname,
                                 http_proxy_port=self._proxy_port,
                                 http_proxy_auth=self._proxy_auth,
                                 sslopt={
                                     "cert_reqs": ssl.CERT_NONE
                                 } if AbstractTokenApiHandler.accept_all_certs else None)

        self._ws = None

        if self._inner_exception:
            raise self._inner_exception

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

    def _close(self):
        """
        Internal stop that does not join the reader thread. Intended to be called on unrecoverable errors within the
        reader thread, i.e. invalid tokens.
        """
        with self._reader_websocket_condition:
            if self._ws:
                self._quit_reader = True
                self._ws.close(status=ABNF.OPCODE_CLOSE,
                               reason="{} closing".format(self._api_handler.get_user_agent()))

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

    def start(self) -> None:
        """
        Start the background thread for receiving messages from the websocket. Returns when the websocket has been
        created.

        :raise RuntimeError: When a reader thread exists already.
        """
        with self._reader_websocket_condition:
            if self._reader_future:
                raise RuntimeError("Reader thread already running")

            self._reader_future = self._reader_executor.submit(AbstractAuthenticatedWebSocketHandler._run, self)
            self._reader_websocket_condition.wait()

    def join(self, timeout: int = None) -> None:
        """
        Joins the reader thread and deletes it thereafter.

        :param timeout: Optional timeout in seconds for joining the reader thread.
        :raise WebSocketException: When the reader thread finished with an exception.
        """
        with self._reader_websocket_condition:
            exception = self._reader_future.exception(timeout)

            self._reconnect_delay = 0
            self._reader_future = None

            if exception:
                raise WebSocketException('Reader thread finished with exception.') from exception

    def stop(self, timeout: int = None) -> None:
        """
        Intentionally closes this websocket. Joins on the reader before returning.

        :param timeout: Optional timeout in seconds for joining the reader thread.
        """
        self._close()
        self.join(timeout)

    def restart(self, timeout: int = None) -> None:
        """
        Closes the websocket and starts a new one.

        :param timeout: Optional timeout in seconds for joining the old reader thread.
        """
        self.stop(timeout)
        self.start()

    def send(self, message: str) -> None:
        """
        Send message across the websocket. Make sure, that this is thread-safe.

        :param message: Message as string
        :raise WebSocketException: When *self._auto_reconnect* is False: If a message cannot be sent and all retries
                                   have been exhausted.
        """
        with self._sender_thread_lock:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("Sending message: " + message)

            retries = 0
            retry_delay = 0

            while True:
                retry_delay = self._backoff(retry_delay)

                try:
                    with self._reader_websocket_condition:
                        if not self._ws:
                            raise RuntimeError('No websocket.')

                        self._ws.send(message)

                    return

                except Exception as err:
                    if retries >= self.MAX_RETRIES:
                        if self._auto_reconnect:
                            retries = 0
                            logger.warning('Restarting because of error "%s"', str(err))
                            self.restart(self._timeout)
                        else:
                            raise WebSocketException("Could not send and all retries have been exhausted.")
                    else:
                        logger.warning('Retrying to send message because of error "%s"', str(err))
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
