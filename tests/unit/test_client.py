from typing import Any, Iterator

from hiro_graph_client import PasswordAuthTokenApiHandler, AbstractTokenApiHandler, HiroGraph, SSLConfig
from hiro_graph_client.batchclient import HiroResultCallback, HiroGraphBatch
from testconfig import CONFIG


class RunBatch(HiroResultCallback):
    hiro_batch_client: HiroGraphBatch

    def __init__(self, api_handler: AbstractTokenApiHandler):
        self.hiro_batch_client = HiroGraphBatch(
            callback=self,
            api_handler=api_handler)

    def result(self, data: Any, code: int) -> None:
        print('Data: ' + str(data))
        print('Code: ' + str(code))

    def run(self, commands: Iterator[dict]):
        self.hiro_batch_client.multi_command(commands)


class TestClient:
    hiro_api_handler = PasswordAuthTokenApiHandler(
        root_url=CONFIG.get('URL'),
        username=CONFIG.get('USERNAME'),
        password=CONFIG.get('PASSWORD'),
        client_id=CONFIG.get('CLIENT_ID'),
        client_secret=CONFIG.get('CLIENT_SECRET'),
        secure_logging=False,
        ssl_config=SSLConfig(verify=False)
    )

    def test_simple_query(self):
        hiro_client: HiroGraph = HiroGraph(api_handler=self.hiro_api_handler)

    def test_batch_command(self):
        hiro_batch_client: HiroGraphBatch = HiroGraphBatch(api_handler=self.hiro_api_handler)

        commands: list = [
            {
                "handle_vertices": {
                    "ogit/_xid": "haas1000:connector1:machine1"
                }
            },
            {
                "handle_vertices": {
                    "ogit/_xid": "haas1000:connector2:machine2"
                }
            }
        ]

        query_results: list = hiro_batch_client.multi_command(commands)

        print(query_results)

        assert isinstance(query_results, list)

    def test_batch_command_callback(self):
        batch_runner: RunBatch = RunBatch(api_handler=self.hiro_api_handler)

        commands: list = [
            {
                "handle_vertices": {
                    "ogit/_xid": "haas1000:connector1:machine1"
                }
            },
            {
                "handle_vertices": {
                    "ogit/_xid": "haas1000:connector2:machine2"
                }
            }
        ]

        batch_runner.run(commands)
