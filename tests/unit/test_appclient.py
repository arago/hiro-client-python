# from typing import Any, Iterator
#
# from hiro_graph_client import HiroApp
#

class TestAppClient:
    USERNAME: str = ''
    PASSWORD: str = ''
    CLIENT_ID: str = ''
    CLIENT_SECRET: str = ''
    URL: str = 'https://[server]:8443/api/app/7.0'
    AUTH_URL: str = 'https://[server]:8443/api/auth/6'

    def test_app_config(self):
        pass

        # hiro_client: HiroApp = HiroApp(
        #     username=self.USERNAME,
        #     password=self.PASSWORD,
        #     client_id=self.CLIENT_ID,
        #     client_secret=self.CLIENT_SECRET,
        #     endpoint=self.URL,
        #     auth_endpoint=self.AUTH_URL
        # )
        #
        # query_result: dict = hiro_client.get_config()
        #
        # print(query_result)
        #
        # assert isinstance(query_result, dict)
