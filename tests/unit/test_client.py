# from typing import Any, Iterator
#
# from hiro_graph_client import HiroApiHandler, HiroGraph, HiroGraphBatch, HiroResultCallback, \
#     PasswordAuthTokenHandler, AbstractTokenHandler
#
# hiro_api_handler = HiroApiHandler("https://ec2-52-213-82-23.eu-west-1.compute.amazonaws.com:8443")


# class RunBatch(HiroResultCallback):
#     hiro_batch_client: HiroGraphBatch
#
#     def __init__(self,
#                  api_handler: HiroApiHandler,
#                  token_handler: AbstractTokenHandler):
#         self.hiro_batch_client = HiroGraphBatch(
#             callback=self,
#             api_handler=api_handler,
#             token_handler=token_handler)
#
#     def result(self, data: Any, code: int) -> None:
#         print('Data: ' + str(data))
#         print('Code: ' + str(code))
#
#     def run(self, commands: Iterator[dict]):
#         self.hiro_batch_client.multi_command(commands)


class TestClient:
    # token_handler = PasswordAuthTokenHandler(
    #     username='',
    #     password='',
    #     client_id='',
    #     client_secret='',
    #     api_handler=hiro_api_handler,
    #     secure_logging=False
    # )

    def test_simple_query(self):
        pass

        # hiro_client: HiroGraph = HiroGraph(
        #     api_handler=hiro_api_handler,
        #     token_handler=self.token_handler)
        #
        # query_result: dict = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"', limit=1, meta=True)
        #
        # print(query_result)
        #
        # assert isinstance(query_result, dict)

    def test_batch_command(self):
        pass

        # hiro_batch_client: HiroGraphBatch = HiroGraphBatch(
        #     api_handler=hiro_api_handler,
        #     token_handler=self.token_handler)
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
        #     api_handler=hiro_api_handler,
        #     token_handler=self.token_handler
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
