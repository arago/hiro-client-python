import json
import logging
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Optional, Union, Dict

from apscheduler.job import Job
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from websocket import WebSocketApp

from hiro_graph_client.clientlib import AbstractTokenApiHandler
from hiro_graph_client.websocketlib import AbstractAuthenticatedWebSocketHandler

logger = logging.getLogger(__name__)
""" The logger for this module """


###############################################################################################################
# Message models
###############################################################################################################

class ActionMessageType(str, Enum):
    ACKNOWLEDGED = 'acknowledged'
    NEGATIVE_ACKNOWLEDGED = 'negativeAcknowledged'
    SEND_ACTION_RESULT = 'sendActionResult'
    SUBMIT_ACTION = 'submitAction'
    ERROR = 'error'
    CONFIG_CHANGED = 'configChanged'


class AbstractActionHandlerMessage:
    """
    The structure of an incoming action message
    """
    id: str
    type: ActionMessageType

    def __init__(self,
                 action_id: Optional[str],
                 action_type: ActionMessageType):
        """
        Constructor

        :param action_id: ID. Might be None for messages without an ID.
        :param action_type: Type of action. Required.
               acknowledged, negativeAcknowledged, sendActionResult, submitAction, error, configChanged
        """
        if not action_type:
            raise ValueError('Cannot use an empty action_type.')
        self.id = action_id
        self.type = action_type

    def __str__(self):
        return json.dumps(vars(self))


class AbstractSimpleActionHandlerMessage(AbstractActionHandlerMessage):
    """
    A simple action handler message containing a code and a message.
    """
    code: int
    message: str

    def __init__(self,
                 action_id: str,
                 action_type: ActionMessageType,
                 code: int,
                 message: str):
        """
        Constructor

        :param action_id: ID
        :param action_type: Type of action message
        :param code: Code
        :param message: Message
        """
        super().__init__(action_id, action_type)
        self.code = code
        self.message = message


class ActionHandlerSubmit(AbstractActionHandlerMessage):
    handler: str
    capability: str
    parameters: dict
    timeout: int
    """Milliseconds"""

    _expires_at: int
    """Milliseconds"""

    def __init__(self,
                 action_id: str,
                 handler: str,
                 capability: str,
                 parameters: dict,
                 timeout: int):
        """
        Constructor

        :param action_id: ID
        :param handler: Handler name
        :param capability: Capability name
        :param parameters: Parameter dict
        :param timeout: Timeout in milliseconds
        """
        super().__init__(action_id, ActionMessageType.SUBMIT_ACTION)
        self.handler = handler
        self.capability = capability
        self.parameters = parameters
        self.timeout = timeout

        self._expires_at = int(time.time_ns() / 1000000 + self.timeout)

    @property
    def expires_at(self):
        return self._expires_at


class ActionHandlerResult(AbstractActionHandlerMessage):
    result: dict

    def __init__(self,
                 action_id: str,
                 result: dict):
        """
        Constructor

        :param action_id: ID
        :param result: Result data
        """
        super().__init__(action_id, ActionMessageType.SEND_ACTION_RESULT)
        self.result = result

    def stringify_result(self) -> str:
        return json.dumps({
            "type": self.type,
            "id": self.id,
            "result": json.dumps(self.result)
        })


class ActionHandlerAck(AbstractSimpleActionHandlerMessage):
    def __init__(self,
                 action_id: str,
                 code: int,
                 message: str):
        """
        Constructor

        :param action_id: ID
        :param code: Ack code
        :param message: Ack message
        """
        super().__init__(action_id, ActionMessageType.ACKNOWLEDGED, code, message)


class ActionHandlerNack(AbstractSimpleActionHandlerMessage):
    def __init__(self,
                 action_id: str,
                 code: int,
                 message: str):
        """
        Constructor

        :param action_id: ID
        :param code: Nack code
        :param message: Nack message
        """
        super().__init__(action_id, ActionMessageType.NEGATIVE_ACKNOWLEDGED, code, message)


class ActionHandlerError(AbstractSimpleActionHandlerMessage):
    def __init__(self, action_id: str, code: int, message: str):
        """
        Constructor

        :param action_id: ID
        :param code: Error code
        :param message: Error message
        """
        super().__init__(action_id, ActionMessageType.ERROR, code, message)


class ActionHandlerConfigChanged(AbstractActionHandlerMessage):
    def __init__(self):
        super().__init__(None, ActionMessageType.CONFIG_CHANGED)


class ActionHandlerMessageParser:
    """
    Create an ActionHandlerMessage from a string message or dict.
    """

    @staticmethod
    def parse(message: Union[dict, str]) -> Optional[AbstractActionHandlerMessage]:
        """
        Create an ActionHandlerMessage from a string message or dict. Return None if no message can be parsed.
        """
        dict_message: dict = json.dumps(message) if isinstance(message, str) else message
        if dict_message:
            action_type = ActionMessageType(dict_message.get('type'))
            if action_type == ActionMessageType.SUBMIT_ACTION:
                return ActionHandlerSubmit(
                    action_id=dict_message.get('id'),
                    handler=dict_message.get('handler'),
                    capability=dict_message.get('capability'),
                    parameters=dict_message.get('parameters'),
                    timeout=dict_message.get('timeout')
                )
            if action_type == ActionMessageType.SEND_ACTION_RESULT:
                return ActionHandlerResult(
                    action_id=dict_message.get('id'),
                    result=dict_message.get('result')
                )
            if action_type == ActionMessageType.ACKNOWLEDGED:
                return ActionHandlerAck(
                    action_id=dict_message.get('id'),
                    code=dict_message.get('code'),
                    message=dict_message.get('message')
                )
            if action_type == ActionMessageType.NEGATIVE_ACKNOWLEDGED:
                return ActionHandlerNack(
                    action_id=dict_message.get('id'),
                    code=dict_message.get('code'),
                    message=dict_message.get('message')
                )
            if action_type == ActionMessageType.CONFIG_CHANGED:
                return ActionHandlerConfigChanged(
                )
            if action_type == ActionMessageType.ERROR:
                return ActionHandlerError(
                    action_id=dict_message.get('id'),
                    code=dict_message.get('code'),
                    message=dict_message.get('message')
                )

        return None


###############################################################################################################
# Special ActionHandlerMessage storage
###############################################################################################################

class ActionItem:
    """
    An item for the *ExpiringStore* which carries its timeout and retries
    """

    message: AbstractActionHandlerMessage
    expires_at: int
    """ Epoch time after which this item is invalid """
    retries: int
    """ Amount of retries this item can be get via the ActionStore.retryGet(). Default is 4 """

    __scheduled_job: Job

    def __init__(self, job: Job, message: AbstractActionHandlerMessage, expires_at: int, retries: int = 4):
        self.__scheduled_job = job
        self.message = message
        self.expires_at = expires_at
        self.retries = retries

    def __del__(self):
        try:
            self.__scheduled_job.remove()
        except JobLookupError:
            pass


class ActionStore:
    """
    A storage implementation with expiring entries
    """

    __store: Dict[str, ActionItem]
    __store_lock: threading.RLock

    __expiry_scheduler: BackgroundScheduler

    def __init__(self):
        self.__store = {}
        self.__store_lock = threading.RLock()
        self.__expiry_scheduler = BackgroundScheduler()

        if logging.root.level == logging.INFO:
            logging.getLogger('apscheduler').setLevel(logging.WARNING)

        self.__expiry_scheduler.start()

    def __del__(self):
        self.__expiry_scheduler.shutdown()

    def add(self,
            expires_at: int,
            message: AbstractActionHandlerMessage,
            retries: int = 4) -> Optional[AbstractActionHandlerMessage]:

        if expires_at - (time.time_ns() / 1000000) < 0:
            logger.debug("Not adding {} {} because it has expired.".format(message.__class__.__name__, message.id))
            return None

        with self.__store_lock:
            if message.id in self.__store:
                logger.debug(
                    "Not adding {} {} because it already exists.".format(message.__class__.__name__, message.id))
                return None

            job: Job = self.__expiry_scheduler.add_job(
                func=lambda message_id: self.__expiry_remove(message_id),
                kwargs={"message_id": message.id},
                trigger='date',
                run_date=datetime.fromtimestamp(expires_at))

            self.__store[message.id] = ActionItem(job, message, expires_at, retries)

            return message

    def remove(self, message_id: str) -> None:
        with self.__store_lock:
            if message_id in self.__store:
                del self.__store[message_id]

    def __expiry_remove(self, message_id: str) -> None:
        with self.__store_lock:
            if message_id in self.__store:
                message = self.__store.pop(message_id).message
                logger.debug("Discard {} {} because it expired.".format(message.__class__.__name__, message.id))

    def get(self, message_id: str) -> Optional[AbstractActionHandlerMessage]:
        with self.__store_lock:
            item: ActionItem = self.__store.get(message_id)
            return item.message if item else None

    def retry_get(self, message_id: str) -> Optional[AbstractActionHandlerMessage]:
        with self.__store_lock:
            item: ActionItem = self.__store.get(message_id)
            if not item:
                return None

            if item.retries:
                item.retries -= 1
                return self.get(message_id)
            else:
                logger.debug("Discard message {} because no retire left.".format(message_id))
                self.remove(message_id)
                return None

    def clear(self) -> None:
        with self.__store_lock:
            self.__store.clear()


###############################################################################################################
# Main handler class
###############################################################################################################

class AbstractActionWebSocketHandler(AbstractAuthenticatedWebSocketHandler):
    """
    A handler for actions
    """

    submitStore: ActionStore = ActionStore()
    """ Static class variable """
    resultStore: ActionStore = ActionStore()
    """ Static class variable """

    def __init__(self, api_handler: AbstractTokenApiHandler):
        """
        Constructor

        :param api_handler: The TokenApiHandler for this WebSocket.
        """
        super().__init__(api_handler, 'action-ws')

    ###############################################################################################################
    # Websocket Events
    ###############################################################################################################

    def on_open(self, ws: WebSocketApp):
        pass

    def on_close(self, ws: WebSocketApp, code: int, reason: str):
        pass

    def on_message(self, ws: WebSocketApp, message: str):

        action_message: AbstractActionHandlerMessage = ActionHandlerMessageParser.parse(message)
        if not action_message:
            return

        if isinstance(action_message, ActionHandlerSubmit):
            logger.info('Handling "{}" (id: {})'.format(action_message.__class__.__name__, action_message.id))

            self.send(str(ActionHandlerAck(action_message.id, 200, "submitAction acknowledged")))

            submit_exists: bool = (AbstractActionWebSocketHandler.submitStore.get(action_message.id) is not None)
            action_handler_submit = None if submit_exists else AbstractActionWebSocketHandler.submitStore.add(
                action_message.expires_at, action_message
            )
            action_handler_result = AbstractActionWebSocketHandler.resultStore.get(action_message.id)

            if action_handler_submit and not action_handler_result:
                try:
                    submit_result = self.on_submit(action_message.capability, action_message.parameters)

                    if not submit_result:
                        result_params = {
                            "message": "Action successful (no data)",
                            "code": 204
                        }
                    else:
                        result_params = {
                            "message": "Action successful",
                            "code": 200,
                            "data": json.dumps(submit_result)
                        }

                except Exception as err:
                    result_params = {
                        "message": str(err),
                        "code": 500
                    }

                action_handler_result = AbstractActionWebSocketHandler.resultStore.add(
                    action_message.expires_at,
                    ActionHandlerResult(action_message.id, result_params)
                )

                AbstractActionWebSocketHandler.submitStore.remove(action_message.id)

            else:
                if action_handler_result:
                    logger.info('Handling "{}" (id: {}): Already processed'.format(
                        action_message.__class__.__name__,
                        action_message.id
                    ))
                elif submit_exists:
                    logger.info('Handling "{}" (id: {}): Still processing'.format(
                        action_message.__class__.__name__,
                        action_message.id
                    ))
                else:
                    logger.info('Handling "{}" (id: {}): Submit not stored - maybe it has expired?'.format(
                        action_message.__class__.__name__,
                        action_message.id
                    ))

            if isinstance(action_handler_result, ActionHandlerResult):
                self.send(action_handler_result.stringify_result())

        elif isinstance(action_message, ActionHandlerResult):
            logger.info('Handling "{}" (id: {})'.format(action_message.__class__.__name__, action_message.id))

            self.send(str(ActionHandlerNack(action_message.id, 400, "sendActionResult rejected")))

        elif isinstance(action_message, ActionHandlerAck):
            logger.info('Handling "{}" (id: {})'.format(action_message.__class__.__name__, action_message.id))

            AbstractActionWebSocketHandler.resultStore.remove(action_message.id)

        elif isinstance(action_message, ActionHandlerNack):
            logger.info('Handling "{}" (id: {})'.format(action_message.__class__.__name__, action_message.id))

            action_handler_result = AbstractActionWebSocketHandler.resultStore.retry_get(action_message.id)
            if isinstance(action_handler_result, ActionHandlerResult):
                time.sleep(1)
                self.send(action_handler_result.stringify_result())

        elif isinstance(action_message, ActionHandlerConfigChanged):
            logger.info('Handling "{}" (id: {})'.format(action_message.__class__.__name__, action_message.id))
            self.on_config_changed()

        elif isinstance(action_message, ActionHandlerError):
            logger.error('Received error message (id: {}) (code {}): {}'.format(
                action_message.__class__.__name__,
                action_message.id, action_message.code, action_message.message
            ))

        else:
            err_msg = 'Got unknown ActionHandler message "{}".'.format(action_message.__class__.__name__)
            logger.error(err_msg)
            if action_message:
                self.send(str(ActionHandlerNack(action_message.id, 400, err_msg)))

    def on_error(self, ws: WebSocketApp, error: Exception):
        pass

    def on_submit(self, capability: str, parameters: dict) -> dict:
        pass

    def on_config_changed(self):
        pass
