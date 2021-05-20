import json
import logging
import threading
from datetime import datetime
from typing import List, Dict

from apscheduler.schedulers.background import BackgroundScheduler
from websocket import WebSocketApp, WebSocketException

from hiro_graph_client.clientlib import AbstractTokenApiHandler
from hiro_graph_client.websocketlib import AbstractAuthenticatedWebSocketHandler, ErrorMessage

logger = logging.getLogger(__name__)
""" The logger for this module """


class EventMessage:
    """
    The structure of an incoming events message
    """
    id: str
    timestamp: int
    nanotime: int
    body: dict
    type: str
    metadata: dict

    def __init__(self,
                 event_id: str,
                 event_timestamp: int,
                 event_body: dict,
                 event_type: str,
                 event_metadata: dict,
                 event_nanotime: int):
        """
        Constructor

        :param event_id: ID
        :param event_timestamp: Timestamp in milliseconds
        :param event_body: Body dict
        :param event_type: Type of event. CREATE, UPDATE or DELETE.
        :param event_metadata: Additional metadata.
        :param event_nanotime: Nanotime for the event
        """
        self.id = event_id
        self.timestamp = event_timestamp
        self.body = event_body
        self.type = event_type.upper()
        self.metadata = event_metadata
        self.nanotime = event_nanotime

    @classmethod
    def parse(cls, message: str):
        """
        :param message: The message received from the websocket. Will be decoded here.
        :return: The EventMessage or None if this is not an EventMessage (type or id are missing).
        """
        json_message: dict = json.loads(message)
        if not isinstance(json_message, dict):
            return None

        event_type = json_message.get('type')
        event_id = json_message.get('id')
        if not event_type or not event_id:
            return None

        return cls(event_id,
                   json_message.get('timestamp'),
                   json_message.get('body'),
                   event_type,
                   json_message.get('metadata'),
                   json_message.get('nanotime'))

    def __str__(self):
        return json.dumps(vars(self))


class EventsFilter:
    """
    The event filter structure
    """
    id: str
    type: str
    content: str

    def __init__(self, filter_id: str, filter_content: str, filter_type: str = None):
        """
        Constructor

        :param filter_id: Unique name/id of the filter
        :param filter_content: jfilter specification for the filter.
        :param filter_type: Type of filter. Only 'jfilter' (the default when this is None) is possible here atm.
        """
        self.id = filter_id
        self.content = filter_content
        self.type = filter_type or 'jfilter'

    def __str__(self):
        return json.dumps(vars(self))

    def to_dict(self) -> dict:
        return {
            "filter-id": self.id,
            "filter-type": self.type,
            "filter-content": self.content
        }


class AbstractEventsWebSocketHandler(AbstractAuthenticatedWebSocketHandler):
    """
    A handler for issue events
    """
    _events_filter_messages: Dict[str, EventsFilter] = {}
    _events_filter_messages_lock: threading.RLock

    _token_scheduler: BackgroundScheduler

    def __init__(self,
                 api_handler: AbstractTokenApiHandler,
                 events_filters: List[EventsFilter]):
        """
        Constructor

        :param api_handler: The TokenApiHandler for this WebSocket.
        :param events_filters: Filters for the events. These have to be set or the flood of incoming events will be too
                               big.
        """
        super().__init__(api_handler, 'events-ws')

        self._events_filter_messages_lock = threading.RLock()

        self._token_scheduler = BackgroundScheduler()

        if logging.root.level == logging.INFO:
            logging.getLogger('apscheduler').setLevel(logging.WARNING)

        for events_filter in events_filters:
            self._events_filter_messages[events_filter.id] = events_filter

    ###############################################################################################################
    # Websocket Events
    ###############################################################################################################

    def on_open(self, ws: WebSocketApp):
        """
        Register the filters when websocket opens. If this fails, the websocket gets closed again.

        :param ws: The WebSocketApp
        :raise WebSocketFilterException: When setting the filters failed.
        """
        try:
            if not self._token_scheduler.running:
                self._set_next_token_refresh()
                self._token_scheduler.start()

            with self._events_filter_messages_lock:
                for events_filter in self._events_filter_messages.values():
                    message = self._get_events_register_message(events_filter)
                    self.send(message)

        except Exception as err:
            raise WebSocketFilterException('Setting events filter failed') from err

    def on_close(self, ws: WebSocketApp, code: int, reason: str):
        """
        Cancel the self._token_refresh_thread. Registered filters remain as they are.

        :param ws: The WebSocketApp
        :param code:
        :param reason:
        """
        if self._token_scheduler.running:
            self._token_scheduler.shutdown()

    def on_message(self, ws: WebSocketApp, message: str):
        """
        Create an EventMessage from the incoming message and hand it over to *self.on_event*.

        :param ws: The WebSocketApp
        :param message: The raw message as string
        """

        event_message = EventMessage.parse(message)
        if event_message:
            if event_message.type not in ['CREATE', 'UPDATE', 'DELETE']:
                logger.error("Unknown event message of type '%s'", event_message.type)
            else:
                self.on_event(event_message)
        else:
            error_message = ErrorMessage.parse(message)
            if error_message:
                logger.error("Received error: %s", str(error_message))
            else:
                logger.error("Invalid message: %s", message)

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

    def on_event(self, message: EventMessage) -> None:
        """
        Catches all event messages. Distributes them between *self.on_create*, *self.on_update* or *self.on_delete*
        by default.
        Overwrite this if you want a catch-all for all event messages.

        :param message: The incoming EventMessage
        """
        if message.type == 'CREATE':
            self.on_create(message)
        elif message.type == 'UPDATE':
            self.on_update(message)
        elif message.type == 'DELETE':
            self.on_delete(message)

    def on_create(self, message: EventMessage) -> None:
        """
        Called by CREATE events. Skeleton function to be overwritten if needed.

        :param message: The incoming EventMessage
        """
        pass

    def on_update(self, message: EventMessage) -> None:
        """
        Called by UPDATE events. Skeleton function to be overwritten if needed.

        :param message: The incoming EventMessage
        """
        pass

    def on_delete(self, message: EventMessage) -> None:
        """
        Called by DELETE events. Skeleton function to be overwritten if needed.

        :param message: The incoming EventMessage
        """
        pass

    ###################################################################################################################
    # Filter handling
    ###################################################################################################################

    @staticmethod
    def _get_events_register_message(events_filter: EventsFilter) -> str:
        message: dict = {
            "type": "register",
            "args": events_filter.to_dict()
        }

        return json.dumps(message)

    def add_events_filter(self, events_filter: EventsFilter) -> None:
        message: str = self._get_events_register_message(events_filter)
        self.send(message)
        with self._events_filter_messages_lock:
            self._events_filter_messages[events_filter.id] = events_filter

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
        if self._api_handler.refresh_time() is not None:
            # make seconds
            timestamp = self._api_handler.refresh_time() / 1000

            self._token_scheduler.add_job(
                func=lambda: self._token_refresh_thread(),
                trigger='date',
                run_date=datetime.fromtimestamp(timestamp),
                id='token_refresh_thread',
                replace_existing=True)

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
    #
    # This is not needed, since events are only received, not sent.
    #
    # def send_events_message(self, events_type: str, headers: dict, body: dict) -> str:
    #     uuid: str = uuid4().hex
    #
    #     message: dict = {
    #         "id": uuid,
    #         "type": events_type,
    #         "headers": headers,
    #         "body": body
    #     }
    #
    #     self.send(json.dumps(message))
    #
    #     return uuid


###################################################################################################################
# Exceptions
###################################################################################################################

class WebSocketFilterException(WebSocketException):
    """
    On errors with setting or parsing filter information.
    """
    pass
