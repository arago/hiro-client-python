# from typing import Any, Iterator
#
# from hiro_graph_client import HiroGraph, HiroGraphBatch, HiroResultCallback
#
#
# class RunBatch(HiroResultCallback):
#     hiro_batch_client: HiroGraphBatch
#
#     def __init__(self,
#                  username: str,
#                  password: str,
#                  client_id: str,
#                  client_secret: str,
#                  graph_endpoint: str,
#                  auth_endpoint: str):
#         self.hiro_batch_client = HiroGraphBatch(
#             callback=self,
#             graph_endpoint=graph_endpoint,
#             auth_endpoint=auth_endpoint,
#             username=username,
#             password=password,
#             client_id=client_id,
#             client_secret=client_secret
#         )
#
#     def result(self, data: Any, code: int) -> None:
#         print('Data: ' + str(data))
#         print('Code: ' + str(code))
#
#     def run(self, commands: Iterator[dict]):
#         self.hiro_batch_client.multi_command(commands)


class TestClient:
    USERNAME: str = ''
    PASSWORD: str = ''
    CLIENT_ID: str = ''
    CLIENT_SECRET: str = ''
    URL: str = 'https://[server]:8443/api/graph/7.2'
    AUTH_URL: str = 'https://[server]:8443/api/auth/6'

    def test_simple_query(self):
        pass

        # hiro_client: HiroGraph = HiroGraph(
        #     username=self.USERNAME,
        #     password=self.PASSWORD,
        #     client_id=self.CLIENT_ID,
        #     client_secret=self.CLIENT_SECRET,
        #     graph_endpoint=self.URL,
        #     auth_endpoint=self.AUTH_URL
        # )
        #
        # query_result: dict = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"', limit=1, meta=True)
        #
        # print(query_result)
        #
        # assert isinstance(query_result, dict)

    def test_batch_command(self):
        pass

        # hiro_batch_client = HiroGraphBatch(
        #     username=self.USERNAME,
        #     password=self.PASSWORD,
        #     client_id=self.CLIENT_ID,
        #     client_secret=self.CLIENT_SECRET,
        #     graph_endpoint=self.URL,
        #     auth_endpoint=self.AUTH_URL
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
        # query_results: list = hiro_batch_client.multi_command(commands)
        #
        # print(query_results)
        #
        # assert isinstance(query_results, list)

    def test_batch_command_callback(self):
        pass

        # batch_runner: RunBatch = RunBatch(
        #     graph_endpoint=self.URL,
        #     auth_endpoint=self.AUTH_URL,
        #     username=self.USERNAME,
        #     password=self.PASSWORD,
        #     client_id=self.CLIENT_ID,
        #     client_secret=self.CLIENT_SECRET
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
