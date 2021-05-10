#!/usr/bin/env python3

from typing import Any, Iterator
from urllib.parse import quote_plus

from hiro_graph_client.clientlib import AuthenticatedAPIHandler, AbstractTokenApiHandler


class HiroGraph(AuthenticatedAPIHandler):
    """
    Python implementation for accessing the HIRO HIRO REST API.
    See https://core.arago.co/help/specs/?url=definitions/graph.yaml
    """

    def __init__(self, api_handler: AbstractTokenApiHandler):
        """
        Constructor

        :param api_handler: External API handler.
        """
        super().__init__(api_name='graph',
                         api_handler=api_handler)

    ###############################################################################################################
    # REST API operations
    ###############################################################################################################

    def query(self,
              query: str,
              fields: str = None,
              limit=-1,
              offset=0,
              order: str = None,
              meta=False) -> dict:
        """
        HIRO REST query API: `POST self._endpoint + '/query/vertices'`

        :param query: The actual query. e.g. ogit\\\\/_type: ogit\\\\/Question for vertices.
        :param fields: the comma separated list of fields to return
        :param limit: limit of entries to return
        :param offset: offset where to start returning entries
        :param order: order by a field asc|desc, e.g. ogit/name desc
        :param meta: List detailed metainformations in result payload
        :return: Result payload
        """
        url = self.endpoint + '/query/vertices'
        data = {"query": str(query),
                "limit": limit,
                "fields": (quote_plus(fields.replace(" ", ""), safe="/,") if fields else ""),
                "count": False,
                "listMeta": meta,
                "offset": offset}
        if order is not None:
            data['order'] = order
        return self.post(url, data)

    def query_gremlin(self,
                      query: str,
                      root: str,
                      fields: str = None,
                      include_deleted: bool = False,
                      meta=False) -> dict:
        """
        HIRO REST query API: `POST self._endpoint + '/query/gremlin'`

        :param query: The actual query. e.g. outE().inV() for gremlin.
        :param root: ogit/_id of the root node where the gremlin query starts.
        :param fields: the comma separated list of fields to return
        :param include_deleted: Include deleted values.
        :param meta: List detailed metainformations in result payload
        :return: Result payload
        """
        url = self.endpoint + '/query/gremlin'
        data = {"query": str(query),
                "root": root,
                "fields": (quote_plus(fields.replace(" ", ""), safe="/,") if fields else ""),
                "includeDeleted": include_deleted,
                "listMeta": meta}
        return self.post(url, data)

    def create_node(self, data: dict, obj_type: str, return_id=False) -> dict:
        """
        HIRO REST query API: `POST self._endpoint + '/new/{id}'`

        :param data: Payload for the new node/vertex
        :param obj_type: ogit/_type of the new node/vertex
        :param return_id: Return only the ogit/_id. Default is False to return everything.
        :return: The result payload
        """
        url = self.endpoint + '/new/' + quote_plus(obj_type)
        res = self.post(url, data)
        return res['ogit/_id'] if return_id and 'error' not in res else res

    def update_node(self, node_id: str, data: dict) -> dict:
        """
        HIRO REST query API: `POST self._endpoint + '/{id}'`

        :param data: Payload for the node/vertex
        :param node_id: ogit/_id of the node/vertex
        :return: The result payload
        """
        url = self.endpoint + '/' + quote_plus(node_id)
        return self.post(url, data)

    def delete_node(self, node_id: str) -> dict:
        """
        HIRO REST query API: `DELETE self._endpoint + '/{id}'`

        :param node_id: ogit/_id of the node/vertex
        :return: The result payload
        """
        url = self.endpoint + '/' + quote_plus(node_id)
        return self.delete(url)

    def connect_nodes(self, from_node_id: str, verb: str, to_node_id: str) -> dict:
        """
        HIRO REST query API: `POST self._endpoint + '/connect/{verb}'`

        :param from_node_id: ogit/_id of the source node/vertex
        :param verb: verb for the connection
        :param to_node_id: ogit/_id of the target node/vertex
        :return: The result payload
        """
        url = self.endpoint + '/connect/' + quote_plus(verb)
        data = {"out": from_node_id, "in": to_node_id}
        return self.post(url, data)

    def disconnect_nodes(self, from_node_id: str, verb: str, to_node_id: str) -> dict:
        """
        HIRO REST query API: `DELETE self._endpoint + '/{id}'`

        :param from_node_id: ogit/_id of the source node/vertex
        :param verb: verb for the connection
        :param to_node_id: ogit/_id of the target node/vertex
        :return: The result payload
        """
        url = self.endpoint + '/' + quote_plus(
            from_node_id
        ) + "$$" + quote_plus(
            verb
        ) + "$$" + quote_plus(
            to_node_id
        )
        return self.delete(url)

    def get_node(self, node_id: str, fields: str = None, meta: bool = None) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}'`

        :param node_id: ogit/_id of the node/vertex or edge
        :param fields: Filter for fields
        :param meta: List detailed metainformations in result payload
        :return: The result payload
        """
        query = {
            "fields": fields.replace(" ", "") if fields else None,
            "listMeta": "true" if meta else None
        }

        url = self.endpoint + '/' + quote_plus(node_id) + self._get_query_part(query)
        return self.get(url)

    def get_nodes(self, node_ids: list, fields: str = None, meta: bool = None) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}'`

        :param node_ids: list of ogit/_ids of the node/vertexes or edges
        :param fields: Filter for fields
        :param meta: List detailed metainformations in result payload
        :return: The result payload
        """
        query = {
            "query": ",".join(node_ids),
            "fields": fields.replace(" ", "") if fields else None,
            "listMeta": "true" if meta else None
        }

        url = self.endpoint + '/query/ids' + self._get_query_part(query)
        return self.get(url)

    def get_node_by_xid(self, node_id: str, fields: str = None, meta: bool = None) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/xid/{xid}'`

        :param node_id: ogit/_xid of the node/vertex or edge
        :param fields: Filter for fields
        :param meta: List detailed metainformations in result payload
        :return: The result payload
        """
        query = {
            "fields": fields.replace(" ", "") if fields else None,
            "listMeta": "true" if meta else None
        }

        url = self.endpoint + '/xid/' + quote_plus(node_id) + self._get_query_part(query)
        return self.get(url)

    def get_timeseries(self, node_id: str, starttime: str = None, endtime: str = None) -> dict:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}/values'`

        :param node_id: ogit/_id of the node containing timeseries
        :param starttime: ms since epoch.
        :param endtime: ms since epoch.
        :return: The result payload
        """
        query = {
            "from": starttime,
            "to": endtime
        }

        url = self.endpoint + '/' + quote_plus(node_id) + '/values' + self._get_query_part(query)
        res = self.get(url)
        if 'error' in res:
            return res
        timeseries = res['items']
        timeseries.sort(key=lambda x: x['timestamp'])
        return timeseries

    def post_timeseries(self, node_id: str, items: list) -> dict:
        """
        HIRO REST query API: `POST self._endpoint + '/{id}/values'`

        :param node_id: ogit/_id of the node containing timeseries
        :param items: list of timeseries values [{timestamp: (ms since epoch), value: ...},...]
        :return: The result payload
        """
        url = self.endpoint + '/' + quote_plus(node_id) + '/values?synchronous=true'
        data = {"items": items}
        return self.post(url, data)

    def get_attachment(self,
                       node_id: str,
                       content_id: str = None,
                       include_deleted: bool = False) -> Iterator[bytes]:
        """
        HIRO REST query API: `GET self._endpoint + '/{id}/content'`

        :param node_id: Id of the attachment node
        :param content_id: Id of the content within the attachment node. Default is None.
        :param include_deleted: Whether to be able to access deleted content: Default is False
        :return: Returns generator over byte chunks from the response body payload.
        """
        query = {
            "contentId": content_id,
            "includeDeleted": "true" if include_deleted else None
        }

        url = self.endpoint + '/' + quote_plus(node_id) + '/content' + self._get_query_part(query)
        yield from self.get_binary(url)

    def post_attachment(self,
                        node_id: str,
                        data: Any,
                        content_type: str = None) -> dict:
        """
        HIRO REST query API: `POST self._endpoint + '/{id}/content'`

        :param node_id: Id of the attachment node
        :param data: Data to upload in binary form. Can also be an IO object for streaming.
        :param content_type: Content-Type for *data*. Defaults to 'application/octet-stream' if left unset.
        :return: The result payload
        """
        url = self.endpoint + '/' + quote_plus(node_id) + '/content'
        return self.post_binary(url, data, content_type=content_type)
