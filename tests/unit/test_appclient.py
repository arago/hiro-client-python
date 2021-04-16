# from hiro_graph_client import HiroApp
# from hiro_graph_client.clientlib import HiroApiHandler, PasswordAuthTokenHandler

# hiro_api_handler = HiroApiHandler("https://[server]:8443")


class TestAppClient:
    # token_handler = PasswordAuthTokenHandler(
    #     username='',
    #     password='',
    #     client_id='',
    #     client_secret='',
    #     api_handler=hiro_api_handler,
    #     secure_logging=False
    # )

    def test_app_config(self):
        pass

        # hiro_client: HiroApp = HiroApp(
        #     api_handler=hiro_api_handler,
        #     token_handler=self.token_handler
        # )
        #
        # query_result: dict = hiro_client.get_config()
        #
        # print(query_result)
        #
        # assert isinstance(query_result, dict)
