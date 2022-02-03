from hiro_graph_client import PasswordAuthTokenApiHandler, HiroGraph, SSLConfig, GraphConnectionHandler
from .testconfig import CONFIG


class TestClient:
    # connection_handler = GraphConnectionHandler(
    #     root_url=CONFIG.get('URL'),
    #     ssl_config=SSLConfig(verify=False)
    # )

    hiro_api_handler = PasswordAuthTokenApiHandler(
        root_url=CONFIG.get('URL'),
        username=CONFIG.get('USERNAME'),
        password=CONFIG.get('PASSWORD'),
        client_id=CONFIG.get('CLIENT_ID'),
        client_secret=CONFIG.get('CLIENT_SECRET'),
        secure_logging=False,
        ssl_config=SSLConfig(verify=False)
    )

    hiro_api_handler2 = PasswordAuthTokenApiHandler(
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

        hiro_client.get_node(node_id="ckqjkt42s0fgf0883pf0cb0hx_ckqjl014l0hvr0883hxcvmcwq", meta=True)

        hiro_client: HiroGraph = HiroGraph(api_handler=self.hiro_api_handler2)

        hiro_client.get_node(node_id="ckqjkt42s0fgf0883pf0cb0hx_ckqjl014l0hvr0883hxcvmcwq", meta=True)

        # def query(_id: str):
        #     hiro_client.get_node(node_id=_id)
        #
        # t1 = threading.Thread(target=query, args=("ckqjkt42s0fgf0883pf0cb0hx_ckqjl014l0hvr0883hxcvmcwq",))
        # t2 = threading.Thread(target=query, args=("ckqjkt42s0fgf0883pf0cb0hx_ckshomsv84i9x0783cla0g2bv",))
        # t3 = threading.Thread(target=query, args=("ckqjkt42s0fgf0883pf0cb0hx_ckshomsv84i9x0783cla0g2bv",))
        #
        # t1.start()
        # t2.start()
        # t3.start()
