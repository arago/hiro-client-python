from hiro_graph_client import PasswordAuthTokenApiHandler, HiroGraph, SSLConfig
from .testconfig import CONFIG


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

        attributes = {
            "/start_date": None,
            "/end_date": None,
            "/status": None,
            "/inActiveTimespan": None
        }

        hiro_client.update_node(node_id="ckqjkt42s0fgf0883pf0cb0hx_ckshomsv84i9x0783cla0g2bv", data=attributes)
