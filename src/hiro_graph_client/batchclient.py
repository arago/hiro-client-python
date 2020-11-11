import concurrent.futures
import queue
from abc import abstractmethod
from enum import Enum
from typing import Optional, Tuple, Any, Iterator, IO

from hiro_graph_client.client import Graphit, TokenHandler, APIConfig
from requests.exceptions import RequestException


class Result(Enum):
    SUCCESS = "success"
    FAILURE = "fail"


class Action(Enum):
    UNDEFINED = "undefined"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class Entity(Enum):
    UNDEFINED = "undefined"
    VERTEX = "vertex"
    EDGE = "edge"
    TIMESERIES = "timeseries"
    ATTACHMENT = "attachment"


class ResultCallback:

    @abstractmethod
    def result(self, data: Any, code: int) -> None:
        pass


class HiroConnection:
    """
    Contains the Graphit Client and a possibly predefined token.
    """

    token: str = None
    """Set a predefined token for the hiro connection."""
    client: Graphit
    """The python client for REST API"""

    def __init__(self, client: Graphit, token: str = None):
        """
        Contains the Graphit Client and a possibly predefined token.

        :param client: Required: Graphit Client
        :param token: Optional: Predefined token
        """
        self.client = client
        self.token = token

    def get_node(self, node_id: str, fields: str, meta: bool = None) -> dict:
        return self.client.get_node(node_id, fields, meta, token=self.token)

    def get_node_by_xid(self, node_id: str, fields: str, meta: bool = None) -> dict:
        return self.client.get_node_by_xid(node_id, fields, meta, token=self.token)

    def create_node(self, data: dict, obj_type: str) -> dict:
        return self.client.create_node(data, obj_type, token=self.token)

    def update_node(self, node_id: str, data: dict) -> dict:
        return self.client.update_node(node_id, data, token=self.token)

    def delete_node(self, node_id: str) -> dict:
        return self.client.delete_node(node_id, token=self.token)

    def connect_nodes(self, from_node_id: str, verb: str, to_node_id: str) -> dict:
        return self.client.connect_nodes(from_node_id, verb, to_node_id, token=self.token)

    def disconnect_nodes(self, from_node_id: str, verb: str, to_node_id: str):
        return self.client.disconnect_nodes(from_node_id, verb, to_node_id, token=self.token)

    def post_timeseries(self, node_id: str, items: list):
        return self.client.post_timeseries(node_id, items, token=self.token)

    def post_attachment(self, node_id: str, data: Any, content_type: str = None):
        return self.client.post_attachment(node_id, data, content_type, token=self.token)


class AbstractIOCarrier:
    """
    Abstract class that handles IO. When a child of this class is encountered, its IO is opened and read,
    then closed.
    """
    io_base: IO = None

    @abstractmethod
    def open(self) -> IO:
        """
        Abstract base class for opening IO

        :return: The IO opened
        :raises IOError: Any IO Error
        """
        pass

    def close(self) -> None:
        """
        Close the IO
        """
        if self.io_base:
            self.io_base.close()


class SessionData:
    """
    Contains caches and session parameters and the token handler.
    At the moment it carries *xid_cache*, an *edge_store* and a *content_store*. And the *token_handler*.
    """
    xid_cache: dict
    """Cache for xid:id"""

    edge_store: dict
    """Stores a copy of '_edge_data' under the value of 'ogit/_id' as key."""

    content_store: dict
    """Stores a copy of '_content_data' under the value of 'ogit/_id' as key."""

    token_handler: TokenHandler
    """Handles token requests"""

    def __init__(self, api_config: APIConfig):
        """

        :param api_config: Configuration for the API that the TokenHandler uses.
        """
        self.xid_cache = {}
        self.edge_store = {}
        self.content_store = {}
        self.token_handler = TokenHandler.new_from(api_config)

    @classmethod
    def new_with_cache_disabled(cls, api_config: APIConfig):
        new_cls = cls(api_config)
        new_cls.xid_cache = None
        return new_cls

    def get_id(self, ogit_xid: str) -> Optional[str]:
        """
        Get an ogit/_id from an ogit/_xid.

        :param ogit_xid: The ogit/_xid to use.
        :return: The ogit/_id from the cache or None if it is not in the cache.
        """
        return None if self.xid_cache is None else self.xid_cache.get(ogit_xid)

    def has_id(self, ogit_id: str) -> bool:
        """
        Check for existence of ogit_id in the cache.

        :param ogit_id: ogit/_id to look for.
        :return: True if ogit_id exists in the cache, False otherwise.
        """
        return False if self.xid_cache is None else bool(list(self.xid_cache.values()).count(ogit_id))

    def register_xid(self, ogit_xid: str, ogit_id: str) -> None:
        """
        Registers a new xid - id mapping in the *xid_cache* unless it or any params are None.

        :param ogit_xid: The xid (key) of the *xid_cache*.
        :param ogit_id: The id (value) of the *xid_cache*.
        """
        if None not in [self.xid_cache, ogit_xid, ogit_id]:
            self.xid_cache[ogit_xid] = ogit_id

    def register_response(self, attributes: dict, response: dict) -> None:
        """
        Collect all data that shall be saved in the session from the attributes and HIRO response.

        Registers a new xid:id mapping in the *xid_cache* unless it or any params are None.

        Saves any edge data and content data from the attributes under the ogit/_id given by the response.

        :param attributes: Original attributes from the Runner command
        :param response: Response from the backend after the Runner command ran.
        """
        ogit_id = response.get("ogit/_id")
        ogit_xid = response.get("ogit/_xid")
        edge_data = attributes.get("_edge_data")
        content_data = attributes.get("_content_data")

        self.register_xid(ogit_id, ogit_xid)

        if None not in [self.edge_store, ogit_id, edge_data]:
            self.edge_store[ogit_id] = edge_data.copy()

        if None not in [self.content_store, ogit_id, content_data]:
            self.content_store[ogit_id] = content_data.copy()

    def unregister_by_response(self, response: dict) -> None:
        """
        Remove all cached values using HIRO response data.

        :param response: Response data from a removed vertex.
        """
        ogit_id = response.get("ogit/_id")
        if not ogit_id:
            return

        if self.edge_store and ogit_id in self.edge_store.keys():
            del self.edge_store[ogit_id]

        if self.content_store and ogit_id in self.content_store.keys():
            del self.content_store[ogit_id]

        if self.xid_cache:
            for k, v in self.xid_cache.items():
                if v == ogit_id:
                    del self.xid_cache[k]
                    break


class HiroBatchRunner:
    """
    Handles a batch of data intended for the same command.

    This is an abstract class. The real commands need to derive from this.
    """

    entity: Entity
    action: Action

    connection: HiroConnection

    session_data: SessionData

    def __init__(self,
                 entity: Entity,
                 action: Action,
                 session_data: SessionData,
                 connection: HiroConnection):
        """
        Constructor

        :param entity: Entity that gets handled (vertex, edge, timeseries etc.)
        :param action: Action to execute on these entities (create, update, delete)
        :param connection: The hiro client to use.
        :param session_data: Carries session data like caches.
        """
        self.connection = connection
        self.entity = entity
        self.action = action

        self.session_data = session_data

    def get_id_by_xid(self, ogit_xid: str) -> Optional[str]:
        """
        Get an ogit/_id from the *xid_cache* or get it from Graphit when it is not in the cache is or it is
        disabled.

        :param ogit_xid: The xid to use to look for an ogit/_id.
        :return: The ogit/_id found or None
        """
        ogit_id = self.session_data.get_id(ogit_xid)

        if ogit_id is None:
            id_result = self.connection.get_node_by_xid(ogit_xid, 'ogit/_id')
            items: list = id_result.get('items')
            if items is None:
                raise KeyError("Response contains no key 'items': \"{}\"".format(id_result))

            if items:
                ogit_id = items[0].get('ogit/_id')

            self.session_data.register_xid(ogit_xid, ogit_id)

        return ogit_id

    def check_id(self, ogit_id: str) -> Optional[str]:
        """
        Check for existence of an id in *xid_cache* or, if not found there or cache is disabled, in Graphit.

        :param ogit_id: The ogit/_id to check.
        :return: The ogit/_id of the result or None
        """
        if self.session_data.has_id(ogit_id):
            return ogit_id

        id_result = self.connection.get_node(ogit_id, 'ogit/_id')
        return id_result.get('ogit/_id')

    def get_vertex_id(self,
                      attributes: dict,
                      id_key: str = "ogit/_id",
                      xid_key: str = "ogit/_xid") -> Optional[str]:
        """
        Get the ogit/_id from the source data given in *attributes*.

        * If the ogit/_id is present in *attributes*, return it.
        * If ogit/_id is missing but ogit/_xid is present, use the ogit/_xid to get the ogit/_id from Graphit and
          return it.

        :param attributes: Dict of attributes.
        :param id_key: The key for the ogit/_id in *attributes*. Defaults to "ogit/_id".
        :param xid_key: The key for the ogit/_id in *attributes*. Defaults to "ogit/_xid".

        :return: The ogit/_id found or None otherwise.
        """

        ogit_id = attributes.get(id_key)

        if ogit_id is None:
            ogit_xid = attributes.get(xid_key)
            if ogit_xid:
                ogit_id = self.get_id_by_xid(ogit_xid)

        return ogit_id

    def get_and_check_vertex_id(self,
                                attributes: dict,
                                id_key: str = "ogit/_id",
                                xid_key: str = "ogit/_xid") -> str:
        """
        Get the ogit/_id from the source data given in *attributes*.

        * If the ogit/_id is present in *attributes*, return it.
        * If ogit/_id is missing but ogit/_xid is present, use the ogit/_xid to get the ogit/_id from Graphit and
          return it.

        :param attributes: Dict of attributes.
        :param id_key: The key for the ogit/_id in *attributes*. Defaults to "ogit/_id".
        :param xid_key: The key for the ogit/_id in *attributes*. Defaults to "ogit/_xid".

        :return: The ogit/_id found.

        :raises ValueError: When no ogit/_id can be found.
        """

        ogit_id = self.get_vertex_id(attributes, id_key, xid_key)

        if ogit_id is None or not ogit_id:
            raise SourceValueError(
                "\"{}\" not found or empty in attributes and cannot be determined by any \"{}\"".format(id_key,
                                                                                                        xid_key))

        return ogit_id

    @staticmethod
    def get_and_check(attributes: dict, key: str, name: str = 'attributes') -> Any:
        """
        Raise ValueError when key is not in attributes or the value behind the key is empty.

        :param attributes: Dict of attributes.
        :param key: The key to look for in *attributes*.
        :param name: Name of the attributes dict. Default is 'attributes'.
        :return: the value in *attributes* of the key.
        :raises ValueError: When 'key' does not exist in *attributes*.
        """
        attribute = attributes.get(key)
        if not attribute:
            raise SourceValueError("\"{}\" not found or empty in \"{}\".".format(key, name))

        return attribute

    @staticmethod
    def for_each_attribute(attributes: dict, *funcs) -> dict:
        """
        Create a copy of *attributes* where a list of functions is applied to each item. Also does not copy any
        attribute whose key is empty or starts with '_'.

        :param attributes: Dict of attributes.
        :param funcs: Set of functions to apply to each element of *attributes*.
        :return: The resulting copy of *attributes*
        """
        result = {}
        for key, value in attributes.items():
            if not key or key[0] == '_':
                continue

            for func in funcs:
                key, value = func(key, value)
                if key is None:
                    break

            if key is not None:
                result[key] = value

        return result

    def resolve_ids(self, key: str, value: str) -> Tuple[str, str]:
        """
        To be used with self.for_each_attribute()

        Try to resolve_ids keys that start with "id:" or "xid:". Try to find the
        ogit/_id of a vertex by using the value for such a key in graphit. Return a tuple of (key, value) with the key
        without its prefix "id:" or "xid:" and the value resolved to a real "ogit/_id".

        :param key: Attribute key
        :param value: Attribute value
        :return: The changed tuple (key, value).
        """
        if key.startswith("xid:"):
            ogit_id = self.get_id_by_xid(value)

            if ogit_id is None or not ogit_id:
                raise ValueError(
                    "Cannot resolve xid \"{}\" of \"{}\".".format(value, key))

            return key[4:], ogit_id

        elif key.startswith("id:"):
            ogit_id = self.check_id(value)

            if ogit_id is None or not ogit_id:
                raise ValueError(
                    "Cannot find id \"{}\" of \"{}\".".format(value, key))

            return key[3:], ogit_id

        else:
            return key, value

    @staticmethod
    def sanitize_for_update(key: str, value: str) -> Tuple[Optional[str], Optional[str]]:
        """
        To be used with self.for_each_attribute()

        Return (None, None) when key starts with "ogit/_" unless "ogit/_owner", "ogit/_content" or "ogit/_tags".

        :param key: Attribute key
        :param value: Attribute value
        :return: The changed tuple (key, value) or (None, None) when this item should be skipped.
        """
        if key.startswith("ogit/_") and key not in ["ogit/_owner", "ogit/_content", "ogit/_tags"]:
            return None, None

        return key, value

    @staticmethod
    def success_message(entity: Entity, action: Action, data: dict) -> dict:
        """
        Success message format

        ::

            {
                "status": "success",
                "entity": entity.value,
                "action": action.value,
                "data": data
            }

        :param entity: Entity handled
        :param action: Action done
        :param data: JSON to return
        :return: The message
        """
        return {
            "status": Result.SUCCESS.value,
            "entity": entity.value,
            "action": action.value,
            "data": data
        }

    @staticmethod
    def error_message(entity: Entity,
                      action: Action,
                      error: Exception,
                      original: dict,
                      status_code: int = None) -> dict:
        """
        Failure message format

        ::

            {
                "status": "fail",
                "entity": entity.value,
                "action": action.value,
                "data": {
                    "error": error.__class__.__name__,
                    "message": str(error),
                    "original_data": original
                }
            }

        :param entity: Entity handled
        :param action: Action done
        :param error: The exception raised
        :param original: The data that lead to the exception
        :param status_code: HTTP status code if available
        :return: The message
        """
        return {
            "status": Result.FAILURE.value,
            "entity": entity.value,
            "action": action.value,
            "data": {
                "error": error.__class__.__name__,
                "code": status_code,
                "message": str(error),
                "original_data": original
            }
        }

    def run(self, attributes: dict, result_queue: queue.Queue) -> None:
        """
        Run the Command with all data given by *attributes*.

        This is the enclosing code for all batch runners. The implementation of a handling a single entry of
        the *attributes* is defined in derived ...Runner-classes.

        :param attributes: Dict with attributes to handle in HIRO.
        :param result_queue: Queue receiving the results.
        """
        try:
            response: dict = self.run_item(attributes)

            response_code = 200
            message = self.success_message(self.entity, self.action, response)

        except RequestException as error:
            response_code = error.response.status_code if error.response is not None else 999
            message = self.error_message(self.entity,
                                         self.action,
                                         error,
                                         attributes,
                                         response_code)

        except SourceValueError as error:
            response_code = 400
            message = self.error_message(self.entity, self.action, error, attributes, 400)

        except Exception as error:
            response_code = 500
            message = self.error_message(self.entity, self.action, error, attributes, 500)

        result_queue.put((message, response_code))

    @abstractmethod
    def run_item(self, attributes: dict) -> dict:
        """
        Abstract method overwritten by derived runner classes.

        :param attributes: A dict of attributes to handle.
        :return: A response dict - usually directly the structure received from the backend.
        """
        raise RuntimeError("Cannot run within HiroCommandBatch directly.")


class CreateVerticesRunner(HiroBatchRunner):
    """
    Create vertices
    """

    def __init__(self, session_data: SessionData, connection: HiroConnection):
        """
        Create vertices

        :param session_data: Required: Session data / caches.
        :param connection: Required: The handler for the connection to HIRO Graphit.
        """
        super().__init__(Entity.VERTEX, Action.CREATE, session_data, connection)

    def run_item(self, attributes: dict) -> dict:
        """
        :param attributes: A dict of attributes to create a vertex from.
        :return: A response dict - usually directly the structure received from the backend.
        """

        ogit_type = self.get_and_check(attributes, "ogit/_type")
        final_attributes = self.for_each_attribute(attributes, self.resolve_ids)

        response: dict = self.connection.create_node(final_attributes, ogit_type)

        self.session_data.register_response(attributes, response)

        return response


class UpdateVerticesRunner(HiroBatchRunner):
    """
    Update vertices
    """

    def __init__(self, session_data: SessionData, connection: HiroConnection):
        """
        Update vertices

        :param session_data: Required: Session data / caches.
        :param connection: Required: The handler for the connection to HIRO Graphit.
        """
        super().__init__(Entity.VERTEX, Action.UPDATE, session_data, connection)

    def run_item(self, attributes: dict) -> dict:
        """
        :param attributes: A dict of attributes to update a vertex from.
        :return: A response dict - usually directly the structure received from the backend.
        """
        ogit_id = self.get_and_check_vertex_id(attributes)
        final_attributes = self.for_each_attribute(attributes, self.resolve_ids, self.sanitize_for_update)

        response: dict = self.connection.update_node(ogit_id, final_attributes)

        self.session_data.register_response(attributes, response)

        return response


class DeleteVerticesRunner(HiroBatchRunner):
    """
    Delete vertices
    """

    def __init__(self, session_data: SessionData, connection: HiroConnection):
        """
        Delete vertices

        :param session_data: Required: Session data / caches.
        :param connection: Required: The handler for the connection to HIRO Graphit.
        """
        super().__init__(Entity.VERTEX, Action.DELETE, session_data, connection)

    def run_item(self, attributes: dict) -> dict:
        """
        :param attributes: A dict of attributes to delete a vertex from.
        :return: A response dict - usually directly the structure received from the backend.
        """
        ogit_id = self.get_and_check_vertex_id(attributes)

        response: dict = self.connection.delete_node(ogit_id)

        self.session_data.unregister_by_response(response)

        return response


class HandleVerticesRunner(HiroBatchRunner):
    """
    Handle vertices. Either update or create them based on incoming payload entries.
    """

    def __init__(self, session_data: SessionData, connection: HiroConnection):
        """
        Handle vertices. Either update or create them based on incoming payload entries.

        :param session_data: Required: Session data / caches.
        :param connection: Required: The handler for the connection to HIRO Graphit.
        """
        super().__init__(Entity.VERTEX, Action.UNDEFINED, session_data, connection)

    def run_item(self, attributes: dict) -> dict:
        """
        :param attributes: A dict of attributes to handle a vertex from. Updates the vertex when it can be found via
                           ogit/_id or ogit/_xid, creates the vertex otherwise when ogit/_type is present.
        :return: A response dict - usually directly the structure received from the backend.
        """
        self.action = Action.UNDEFINED

        ogit_id = self.get_vertex_id(attributes)

        self.action = Action.UPDATE if ogit_id else Action.CREATE

        if self.action == Action.CREATE:
            ogit_type = self.get_and_check(attributes, "ogit/_type")
            final_attributes = self.for_each_attribute(attributes, self.resolve_ids)

            response: dict = self.connection.create_node(final_attributes, ogit_type)
        else:
            final_attributes = self.for_each_attribute(attributes, self.resolve_ids, self.sanitize_for_update)

            response: dict = self.connection.update_node(ogit_id, final_attributes)

        self.session_data.register_response(attributes, response)

        return response


class CreateEdgesRunner(HiroBatchRunner):
    """
    Create edges between vertices
    """

    def __init__(self, session_data: SessionData, connection: HiroConnection):
        """
        Create edges between vertices

        :param session_data: Required: Session data / caches.
        :param connection: Required: The handler for the connection to HIRO Graphit.
        """
        super().__init__(Entity.EDGE, Action.CREATE, session_data, connection)

    def run_item(self, attributes: dict) -> dict:
        """
        :param attributes: A dict of attributes to create edges from.
        :return: A response dict - usually directly the structure received from the backend.
        """
        from_node_id = self.get_and_check_vertex_id(attributes, "from:ogit/_id", "from:ogit/_xid")
        to_node_id = self.get_and_check_vertex_id(attributes, "to:ogit/_id", "to:ogit/_xid")
        verb = self.get_and_check(attributes, "verb")

        return self.connection.connect_nodes(from_node_id, verb, to_node_id)


class DeleteEdgesRunner(HiroBatchRunner):
    """
    Delete edges between vertices
    """

    def __init__(self, session_data: SessionData, connection: HiroConnection):
        """
        Delete edges between vertices

        :param session_data: Required: Session data / caches.
        :param connection: Required: The handler for the connection to HIRO Graphit.
        """
        super().__init__(Entity.EDGE, Action.DELETE, session_data, connection)

    def run_item(self, attributes: dict) -> dict:
        """
        :param attributes: A dict of attributes to delete edges from.
        :return: A response dict - usually directly the structure received from the backend.
        """
        from_node_id = self.get_and_check_vertex_id(attributes, "from:ogit/_id", "from:ogit/_xid")
        to_node_id = self.get_and_check_vertex_id(attributes, "to:ogit/_id", "to:ogit/_xid")
        verb = self.get_and_check(attributes, "verb")

        return self.connection.disconnect_nodes(from_node_id, verb, to_node_id)


class AddTimeseriesRunner(HiroBatchRunner):
    """
    Attach timeseries values to a vertex.
    """

    def __init__(self, session_data: SessionData, connection: HiroConnection):
        """
        Attach timeseries values to a vertex.

        :param session_data: Required: Session data / caches.
        :param connection: Required: The handler for the connection to HIRO Graphit.
        """
        super().__init__(Entity.TIMESERIES, Action.CREATE, session_data, connection)

    def run_item(self, attributes: dict) -> dict:
        """
        :param attributes: A dict of attributes to attach timeseries to a vertex.
        :return: A response dict - usually directly the structure received from the backend.
        """
        node_id = self.get_and_check_vertex_id(attributes)
        items = self.get_and_check(attributes, "items")

        return self.connection.post_timeseries(node_id, items)


class AddAttachmentRunner(HiroBatchRunner):
    """
    Attach an attachment to a vertex.
    """

    def __init__(self, session_data: SessionData, connection: HiroConnection):
        """
        Attach an attachment to a vertex.

        :param session_data: Required: Session data / caches.
        :param connection: Required: The handler for the connection to HIRO Graphit.
        """
        super().__init__(Entity.ATTACHMENT, Action.CREATE, session_data, connection)

    def run_item(self, attributes: dict) -> dict:
        """
        :param attributes: A dict of attributes to attach attachments to a vertex.
        :return: A response dict - usually directly the structure received from the backend.
        """
        node_id = self.get_and_check_vertex_id(attributes)
        content_data = self.get_and_check(attributes, '_content_data')
        mimetype = content_data.get('mimetype')

        data = content_data.get('data')

        if isinstance(data, AbstractIOCarrier):
            io_item = data.open()
            try:
                return self.connection.post_attachment(node_id=node_id,
                                                       data=io_item,
                                                       content_type=mimetype)
            finally:
                data.close()
        elif data:
            return self.connection.post_attachment(node_id=node_id,
                                                   data=data,
                                                   content_type=mimetype)
        else:
            raise SourceValueError('"data" not found or empty in "attributes._content_data".')


class GraphitBatch:
    """
    This class handles lists of vertex-, edge- or timeseries-data via Graphit.
    """

    api_config: APIConfig

    request_queue: queue.Queue
    result_queue: queue.Queue

    callback: ResultCallback

    use_xid_cache: bool
    """Use xid caching. Default is True when omitted or set to None."""

    commands = [
        "create_vertices",
        "update_vertices",
        "handle_vertices",
        "handle_vertices_combined",
        "delete_vertices",
        "create_edges",
        "delete_edges",
        "add_timeseries",
        "add_attachments"
    ]
    """This is the list of commands (method names) that GraphitBatch handles."""

    def __init__(self,
                 graph_endpoint: str,
                 callback: ResultCallback,
                 hiro_token: str = None,
                 username: str = None,
                 password: str = None,
                 client_id: str = None,
                 client_secret: str = None,
                 auth_endpoint: str = None,
                 iam_endpoint: str = None,
                 use_xid_cache: bool = True,
                 proxies: dict = None,
                 parallel_workers: int = 8,
                 queue_depth: int = None):
        """
        Constructor

        Use the connection to HIRO Graphit either by giving a predefined *hiro_token* or by
        specifying all other parameters needed for authentication.

        :param graph_endpoint: required: URL of the graph.
        :param callback: required: Callback object for results.
        :param hiro_token: optional, required if other authentication data is missing: Predefined token to authenticate
                           against HIRO. Overrides all other authentication data.
        :param username: optional, required if *hiro_token* is None: Username for Graphit .
        :param password: optional, required if *hiro_token* is None: Password for Graphit.
        :param client_id: optional, required if *hiro_token* is None: Id for Authentication (OAuth2).
        :param client_secret: optional, required if *hiro_token* is None: Secret for Authentication (OAuth2).
        :param auth_endpoint: optional, required if *hiro_token* is None: URL of the authentication API.
        :param iam_endpoint: optional: URL of the IAM instance for accessing accounts. Default is None.
        :param use_xid_cache: Use xid caching. Default is True when omitted or set to None.
        :param proxies: Proxy configuration for *requests*. Default is None.
        :param parallel_workers: Amount of parallel workers for requests. Default is 8.
        :param queue_depth: Amount of entries the *self.request_queue* and *self.result_queue* can hold. Default is to
                            set it to the same value as *parallel_workers*.
        """

        if not graph_endpoint:
            raise ValueError('Required attribute "graph_endpoint" is not set.')

        if not (hiro_token or (username and password and client_id and client_secret and auth_endpoint)):
            msg = ""
            if username or password or client_id or client_secret or auth_endpoint:
                if not username:
                    msg = "Incomplete credentials: Username is missing"
                if not password:
                    msg = "Incomplete credentials: Password is missing"
                if not client_id:
                    msg = "Incomplete credentials: Client ID is missing"
                if not client_secret:
                    msg = "Incomplete credentials: Client Secret is missing"
                if not auth_endpoint:
                    msg = "Incomplete credentials: Auth endpoint url is missing"
            else:
                msg = "HIRO_TOKEN is missing"

            raise ValueError("Cannot authenticate against HIRO without credentials or a HIRO_TOKEN. {}".format(msg))

        self.api_config = APIConfig(username=username,
                                    password=password,
                                    client_id=client_id,
                                    client_secret=client_secret,
                                    graph_endpoint=graph_endpoint,
                                    auth_endpoint=auth_endpoint,
                                    iam_endpoint=iam_endpoint,
                                    raise_exceptions=True,
                                    proxies=proxies)

        self.request_queue = queue.Queue(maxsize=queue_depth or parallel_workers)
        self.result_queue = queue.Queue(maxsize=queue_depth or parallel_workers)

        self.callback = callback
        self.hiro_token = hiro_token

        self.parallel_workers = parallel_workers

        self.use_xid_cache = False if use_xid_cache is False else True

    def __init_session(self) -> SessionData:
        """
        Initialize session.

        This session uses a cache with ogit/_xid : ogit/_id mappings when *use_xid_cache* is true.

        :return: The initialized session.
        """
        return SessionData(self.api_config) if self.use_xid_cache is True \
            else SessionData.new_with_cache_disabled(self.api_config)

    def __prepare_session_and_connection(self,
                                         session: SessionData,
                                         connection: HiroConnection) -> Tuple[SessionData, HiroConnection]:
        """
        Initialize session and connection if either of them is unset.

        :param session: Predefined session - if any.
        :param connection:  Predefined connection - if any.
        :return: A tuple of (SessionData, HiroConnection)
        """
        if not session:
            session = self.__init_session()
        if not connection:
            connection = HiroConnection(Graphit.new_from(self.api_config, session.token_handler), self.hiro_token)
        return session, connection

    def create_vertices(self, attributes: dict, connection: HiroConnection = None, session: SessionData = None):
        """
        Create vertex from *attributes*.

        :param attributes: Dict containing the attributes for the vertex.
        :param connection: optional: Connection to use. A new connection will be used if this is not set.
        :param session: optional: Persistent data for the current session. Use a local session if this is not set.
        """
        session, connection = self.__prepare_session_and_connection(session, connection)
        return CreateVerticesRunner(session, connection).run(attributes, self.result_queue)

    def update_vertices(self, attributes: dict, connection: HiroConnection = None, session: SessionData = None):
        """
        Update vertex from *attributes*.

        Attributes needs at least a column "ogit/_id" or "ogit/_xid" to find the vertex to be updated.
        It then sanitizes the payload by ignoring every attribute starting with "ogit/_" (unless "ogit/_owner",
        "ogit/_content" or "ogit/_tags") of the dict before attempting to update.

        :param attributes: Dict containing the attributes for the vertex.
        :param connection: optional: Connection to use. A new connection will be used if this is not set.
        :param session: optional: Persistent data for the current session. Use a local session if this is not set.
        """
        session, connection = self.__prepare_session_and_connection(session, connection)
        return UpdateVerticesRunner(session, connection).run(attributes, self.result_queue)

    def delete_vertices(self, attributes: dict, connection: HiroConnection, session: SessionData = None):
        """
        Delete vertex given by *attributes*.

        Attributes needs at least a column "ogit/_id" or "ogit/_xid" to find the vertex to be deleted.

        :param attributes: Dict containing the attributes for the vertex.
        :param connection: optional: Connection to use. A new connection will be used if this is not set.
        :param session: optional: Persistent data for the current session. Use a local session if this is not set.
        """
        session, connection = self.__prepare_session_and_connection(session, connection)
        return DeleteVerticesRunner(session, connection).run(attributes, self.result_queue)

    def handle_vertices(self, attributes: dict, connection: HiroConnection = None, session: SessionData = None):
        """
        Handles vertex from *attributes*. Tries to update or create.

        When attributes contain "ogit/_id" or "ogit/_xid", they will be used to update an
        existing vertex, otherwise the attributes will be used to create a new vertex.

        :param attributes: Dict containing the attributes for the vertex.
        :param connection: optional: Connection to use. A new connection will be used if this is not set.
        :param session: optional: Persistent data for the current session. Use a local session if this is not set.
        """
        session, connection = self.__prepare_session_and_connection(session, connection)
        return HandleVerticesRunner(session, connection).run(attributes, self.result_queue)

    def create_edges(self, attributes: dict, connection: HiroConnection = None, session: SessionData = None):
        """
        Create edge from *attributes*.

        Attributes needs a column "from:ogit/_id" or "from:ogit/_xid" and
        "to:ogit/_id" or "to:ogit/_xid" as well as "verb" to be able to determine the vertices to connect.

        :param attributes: Dict containing the fields "from:...,verb,to:..." for the edge.
        :param connection: optional: Connection to use. A new connection will be used if this is not set.
        :param session: optional: Persistent data for the current session. Use a local session if this is not set.
        """
        session, connection = self.__prepare_session_and_connection(session, connection)
        return CreateEdgesRunner(session, connection).run(attributes, self.result_queue)

    def delete_edges(self, attributes: dict, connection: HiroConnection = None, session: SessionData = None):
        """
        Delete edge given by *attributes*.

        Attributes needs a column "from:ogit/_id" or "from:ogit/_xid" and
        "to:ogit/_id" or "to:ogit/_xid" as well as "verb" to be able to determine the edge between the vertices to
        delete.

        :param attributes: Dict containing the "from:...,verb,to:..." fields for the edge.
        :param connection: optional: Connection to use. A new connection will be used if this is not set.
        :param session: optional: Persistent data for the current session. Use a local session if this is not set.
        """
        session, connection = self.__prepare_session_and_connection(session, connection)
        return DeleteEdgesRunner(session, connection).run(attributes, self.result_queue)

    def add_timeseries(self, attributes: dict, connection: HiroConnection = None, session: SessionData = None):
        """
        Update vertices with timeseries data.

        Attributes needs at least a column "ogit/_id" or "ogit/_xid" to find the vertex to be updated.

        :param attributes: Contains the timeseries items.
        :param connection: optional: Connection to use. A new connection will be used if this is not set.
        :param session: optional: Persistent data for the current session. Use a local session if this is not set.
        """
        session, connection = self.__prepare_session_and_connection(session, connection)
        return AddTimeseriesRunner(session, connection).run(attributes, self.result_queue)

    def add_attachments(self, attributes: dict, connection: HiroConnection = None, session: SessionData = None):
        """
        Add attachment to vertex.

        Attributes needs at least a key "ogit/_id" or "ogit/_xid" to find the vertex to be updated, and a dict
        '_content_data' containing the payload to update under key 'data' - use an IO class of AbstractIOCarrier
        for streaming.

        Example:
        ::

            {
                "ogit/_id": "",
                "_content_data": {
                    "data": "(payload)",
                    "mimetype": "(content-type)"
                }
            }

        :param attributes: Contains the attachment data.
        :param connection: optional: Connection to use. A new connection will be used if this is not set.
        :param session: optional: Persistent data for the current session. Use a local session if this is not set.
        """
        session, connection = self.__prepare_session_and_connection(session, connection)
        return AddAttachmentRunner(session, connection).run(attributes, self.result_queue)

    def _edges_from_session(self, session: SessionData) -> None:
        """
        Recreate attributes to create edges saved in a session.

        :param session: The session with the edge data.
        """
        for ogit_id, edge_data in session.edge_store.items():
            for edge in edge_data:
                other_ogit_id = edge.get("vertex_id")
                other_ogit_xid = edge.get("vertex_xid")
                verb = edge.get('verb')
                direction = edge.get("direction")

                attributes = {
                    "verb": verb
                }
                if direction == 'in':
                    attributes["to:ogit/_id"] = ogit_id
                    if other_ogit_id:
                        attributes["from:ogit/_id"] = other_ogit_id
                    else:
                        attributes["from:ogit/_xid"] = other_ogit_xid
                else:
                    attributes["from:ogit/_id"] = ogit_id
                    if other_ogit_id:
                        attributes["to:ogit/_id"] = other_ogit_id
                    else:
                        attributes["to:ogit/_xid"] = other_ogit_xid

                self.request_queue.put(('create_edges', attributes))

    def _attachments_from_session(self, session: SessionData) -> None:
        """
        Recreate attributes to create attachments saved in a session.

        :param session: The session with the attachment data.
        """
        for ogit_id, content_data in session.content_store.items():
            attributes = {
                'ogit/_id': ogit_id,
                '_content_data': content_data
            }

            self.request_queue.put(('add_attachments', attributes))

    def _reader(self) -> None:
        """
        Thread executor function. Read items from the *self.result_queue* and call the callback function with them.

        Thread exits when *self.result_queue.get()* reads None.
        """
        for result, code in iter(self.result_queue.get, None):
            self.callback.result(result, code)
            self.result_queue.task_done()

    def _worker(self, session: SessionData) -> None:
        """
        Thread executor function. Create a connection, then read data from the *self.request_queue* and execute
        the command with the attributes and session the data from the queue provides.

        Thread exits when *self.request_queue.get()* reads None.

        :param session: The session object to share between all connections.
        """
        connection = HiroConnection(Graphit.new_from(self.api_config, session.token_handler), self.hiro_token)

        for command, attributes in iter(self.request_queue.get, None):
            func = getattr(self, command, None)
            if func:
                func(attributes, connection, session)
            self.request_queue.task_done()

    def multi_command(self, command_iter: Iterator[dict]) -> None:
        """
        Run a multi-command batch.

        The command_iter iterates over a dict with pairs

        ::

            {
                "[command]": payload,
                "[command]": payload
            }

        with payload being a list of dict containing the attributes to run with that command.

        :param command_iter: An iterator for a dict of pairs "[command]:payload".
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:

            session = self.__init_session()

            executor.submit(GraphitBatch._reader, self)
            for _ in range(self.parallel_workers):
                executor.submit(GraphitBatch._worker, self, session)

            handle_session_data = False
            for command_entry in command_iter:
                for command, attributes in command_entry.items():

                    if command == "handle_vertices_combined":
                        command = "handle_vertices"
                        handle_session_data = True

                    if command in self.commands:
                        self.request_queue.put((command, attributes))
                    else:
                        sub_result, sub_code = HiroBatchRunner.error_message(
                            Entity.UNDEFINED,
                            Action.UNDEFINED,
                            SourceValueError("No such command \"{}\".".format(command)),
                            attributes,
                            400), 400

                        self.result_queue.put((sub_result, sub_code))

            if handle_session_data:
                self.request_queue.join()
                self._edges_from_session(session)
                self._attachments_from_session(session)

            self.request_queue.join()
            self.result_queue.join()

            for _ in range(self.parallel_workers):
                self.request_queue.put(None)

            self.result_queue.put(None)


class SourceValueError(ValueError):
    """
    An error occurred with missing or invalid source data.
    """
    pass
