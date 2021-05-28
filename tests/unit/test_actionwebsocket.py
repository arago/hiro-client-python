# from hiro_graph_client.actionwebsocket import AbstractActionWebSocketHandler
# from hiro_graph_client.clientlib import PasswordAuthTokenApiHandler, AbstractTokenApiHandler, accept_all_certs


# class ActionWebSocket(AbstractActionWebSocketHandler):
#
#     def __init__(self, api_handler: AbstractTokenApiHandler):
#         super().__init__(api_handler)
#
#     def on_submit_action(self, action_id: str, capability: str, parameters: dict):
#         print(f"ID: {action_id}, Capability: {capability}, Parameters: {str(parameters)}")
#
#         self.send_action_result(action_id, "Everything went fine.")
#         #     raise Exception("This is a test exception.")
#
#     def on_config_changed(self):
#         pass


class TestActionWebsocket:
    # api_handler = PasswordAuthTokenApiHandler(
    #     root_url="",
    #     username='',
    #     password='',
    #     client_id='',
    #     client_secret='',
    #     secure_logging=False
    # )
    #
    def test_actions(self):
        # accept_all_certs()
        #
        # with ActionWebSocket(api_handler=self.api_handler) as ws:
        #     input("Press [Enter] to stop.\n")
        pass
