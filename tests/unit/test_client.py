# from typing import Any, Iterator
#
# from hiro_graph_client import HiroGraph, HiroGraphBatch, HiroResultCallback, PasswordAuthTokenHandler, \
#     AbstractTokenHandler
#
#
# class RunBatch(HiroResultCallback):
#     hiro_batch_client: HiroGraphBatch
#
#     def __init__(self,
#                  graph_endpoint: str,
#                  token_handler: AbstractTokenHandler):
#         self.hiro_batch_client = HiroGraphBatch(
#             callback=self,
#             endpoint=graph_endpoint,
#             token_handler=token_handler)
#
#     def result(self, data: Any, code: int) -> None:
#         print('Data: ' + str(data))
#         print('Code: ' + str(code))
#
#     def run(self, commands: Iterator[dict]):
#         self.hiro_batch_client.multi_command(commands)


class TestClient:
    # USERNAME: str = ''
    # PASSWORD: str = ''
    # CLIENT_ID: str = ''
    # CLIENT_SECRET: str = ''
    # URL: str = 'https://[server]:8443/api/graph/7.2'
    # AUTH_URL: str = 'https://[server]:8443/api/auth/6'
    #
    # _token_handler = PasswordAuthTokenHandler(
    #     username=USERNAME,
    #     password=PASSWORD,
    #     client_id=CLIENT_ID,
    #     client_secret=CLIENT_SECRET,
    #     endpoint=AUTH_URL)

    def test_simple_query(self):
        pass

        # hiro_client: HiroGraph = HiroGraph(
        #     endpoint=self.URL,
        #     token_handler=self._token_handler)
        #
        # query_result: dict = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"', limit=1, meta=True)
        #
        # print(query_result)
        #
        # assert isinstance(query_result, dict)

    def test_batch_command(self):
        pass

        # hiro_batch_client: HiroGraphBatch = HiroGraphBatch(
        #     endpoint=self.URL,
        #     token_handler=self._token_handler)
        #
        # commands: list = [
        #     {
        #         "handle_vertices": {
        #             "ogit/_xid": "haas1000:connector1:machine1"
        #         }
        #     },
        #     {
        #         "handle_vertices": {
        #             "ogit/_xid": "haas1000:connector2:machine2"
        #         }
        #     }
        # ]
        #
        # query_results: list = hiro_batch_client.multi_command(commands)
        #
        # print(query_results)
        #
        # assert isinstance(query_results, list)

    def test_batch_command_callback(self):
        pass

        # batch_runner: RunBatch = RunBatch(
        #     graph_endpoint=self.URL,
        #     token_handler=self._token_handler
        # )
        #
        # commands: list = [
        #     {
        #         "handle_vertices": {
        #             "ogit/_xid": "haas1000:connector1:machine1"
        #         }
        #     },
        #     {
        #         "handle_vertices": {
        #             "ogit/_xid": "haas1000:connector2:machine2"
        #         }
        #     }
        # ]
        #
        # batch_runner.run(commands)
