import json
import logging
import sched
import threading
import time
from abc import abstractmethod
from typing import Optional
from uuid import uuid4

from hiro_graph_client.clientlib import AbstractTokenApiHandler
from hiro_graph_client.websocketlib import AbstractHandledWebSocket, CloseWebSocketException
from websocket import WebSocketApp, WebSocketException

logger = logging.getLogger(__name__)
""" The logger for this module """


class EventMessage:
    """
    The structure of an incoming events message
    """
    id: str
    timestamp: int
    body: dict
    type: str
    metadata: dict

    def __init__(self, message: str):
        """
        Constructor

        :param message: The message received from the websocket. Will be decoded here.
        """
        json_message: dict = json.loads(message)
        self.id = str(json_message['id'])
        self.timestamp = int(json_message['timestamp'])
        self.body = dict(json_message['body'])
        self.type = str(json_message['type']).upper()
        self.metadata = dict(json_message['metadata'])


class AbstractEventWebSocket(AbstractHandledWebSocket):
    """
    A handler for issue events
    """
    _events_filter_messages: dict
    _events_filter_messages_lock: threading.RLock

    _token_scheduler: sched.scheduler

    _token_event: Optional[sched.Event] = None
    _token_event_lock: threading.RLock

    def __init__(self,
                 api_handler: AbstractTokenApiHandler,
                 events_filters: list):
        """
        Constructor

        :param api_handler: The TokenApiHandler for this WebSocket.
        :param events_filters: Filters for the events. These have to be set or the flood of incoming events will be too
                               big.
        """
        super().__init__(api_handler, 'events-ws')

        self._events_filter_messages_lock = threading.RLock()

        self._token_event_lock = threading.RLock()

        self._token_scheduler = sched.scheduler(timefunc=time.time)

        for events_filter in events_filters:
            self._events_filter_messages[self._get_filter_id(events_filter)] = events_filter

    def on_open(self, ws: WebSocketApp):
        """
        Register the filters when websocket opens. If this fails, the websocket gets closed again.

        :param ws: The WebSocketApp
        """
        try:
            with self._events_filter_messages_lock:
                for events_filter in self._events_filter_messages:
                    message = self._get_events_register_message(events_filter)
                    self.send(message)

                self._set_next_token_refresh()

        except Exception as err:
            raise CloseWebSocketException('Setting events filter failed') from err

    def on_close(self, ws: WebSocketApp, code: int, reason: str):
        """
        Cancel the self._token_refresh_thread. Registered filters remain as they are.

        :param ws: The WebSocketApp
        :param code:
        :param reason:
        """
        with self._token_event_lock:
            if self._token_event:
                self._token_scheduler.cancel(self._token_event)

    def on_message(self, ws: WebSocketApp, message: str):
        """
        Create an EventMessage from the incoming message and hand it over to *self.on_create*, *self.on_update* or
        *self.on_delete*.

        :param ws: The WebSocketApp
        :param message: The raw message as string
        """
        event_message = EventMessage(message)

        if event_message.type == 'CREATE':
            self.on_create(event_message)
        elif event_message.type == 'UPDATE':
            self.on_update(event_message)
        elif event_message.type == 'DELETE':
            self.on_delete(event_message)
        else:
            raise InvalidEventWebSocketException("Unknown event message of type '{}'".format(event_message.type))

    def on_error(self, ws: WebSocketApp, error: Exception):
        """
        Does nothing here.

        :param ws: The WebSocketApp
        :param error: Exception
        """
        pass

    ###############################################################################################################
    # Public API Reader thread
    ###############################################################################################################

    @abstractmethod
    def on_create(self, message: EventMessage):
        pass

    @abstractmethod
    def on_update(self, message: EventMessage):
        pass

    @abstractmethod
    def on_delete(self, message: EventMessage):
        pass

    ###################################################################################################################
    # Filter handling
    ###################################################################################################################
    def _get_filter_id(self, events_filter: dict) -> str:
        events_filter_id: str = events_filter.get("filter-id")
        if not events_filter_id:
            raise WebSocketFilterException("This filter has no 'filter-id'.")

        return events_filter_id

    def _get_events_register_message(self, events_filter: dict) -> str:
        message: dict = {
            "type": "register",
            "args": events_filter
        }

        return json.dumps(message)

    def add_events_filter(self, events_filter: dict) -> None:
        events_filter_id: str = self._get_filter_id(events_filter)
        message: str = self._get_events_register_message(events_filter)
        self.send(message)
        with self._events_filter_messages_lock:
            self._events_filter_messages[events_filter_id] = message

    def remove_events_filter(self, events_filter_id: str) -> None:
        message: dict = {
            "type": "unregister",
            "args": {
                "filter-id": events_filter_id
            }
        }

        self.send(json.dumps(message))
        with self._events_filter_messages_lock:
            del self._events_filter_messages[events_filter_id]

    def clear_events_filters(self) -> None:
        message: dict = {
            "type": "clear",
            "args": {}
        }

        self.send(json.dumps(message))
        with self._events_filter_messages_lock:
            self._events_filter_messages = {}

    ###################################################################################################################
    # Token refresh thread
    ###################################################################################################################

    def _set_next_token_refresh(self):
        with self._token_event_lock:
            if self._api_handler.refresh_time() is not None:
                self._token_event = self._token_scheduler.enterabs(
                    time=self._api_handler.refresh_time(),
                    priority=2,
                    action=self._token_refresh_thread(),
                    argument=(self,)
                )
            else:
                self._token_event = None

    def _token_refresh_thread(self):
        logger.debug("Updating token for session")

        message: dict = {
            "type": "token",
            "args": {
                "_TOKEN": self._api_handler.token
            }
        }

        self.send(json.dumps(message))

        self._set_next_token_refresh()

    ###################################################################################################################
    # Sending messages
    ###################################################################################################################

    def send_events_message(self, events_type: str, headers: dict, body: dict) -> str:
        uuid: str = uuid4().hex

        message: dict = {
            "id": uuid,
            "type": events_type,
            "headers": headers,
            "body": body
        }

        self.send(json.dumps(message))

        return uuid


###################################################################################################################
# Exceptions
###################################################################################################################

class WebSocketFilterException(WebSocketException):
    """
    On errors with setting or parsing filter information.
    """
    pass


class InvalidEventWebSocketException(WebSocketException):
    """
    When an EventMessage with an unknown type has been received.
    """
    pass
