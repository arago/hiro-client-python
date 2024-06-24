import base64
import gzip
import json

from hiro_graph_client import CodeFlowAuthTokenApiHandler, PasswordAuthTokenApiHandler, SSLConfig, \
    GraphConnectionHandler, HiroApp, HiroAuth
from .testconfig import CONFIG_STAGE as CONFIG


class TestClient:

    connection_handler = GraphConnectionHandler(
        root_url=CONFIG.get('URL'),
        ssl_config=SSLConfig(verify=False)
    )

    def test_download_config(self):
        hiro_api_handler = PasswordAuthTokenApiHandler(
            username=CONFIG.get('USERNAME'),
            password=CONFIG.get('PASSWORD'),
            client_id=CONFIG.get('CLIENT_ID'),
            client_secret=CONFIG.get('CLIENT_SECRET'),
            secure_logging=False,
            connection_handler=self.connection_handler
        )

        hiro_app: HiroApp = HiroApp(api_handler=hiro_api_handler)

        result = hiro_app.get_config()

        content = result.get("content")
        content_type = result.get("type")

        content_bytes = base64.b64decode(content) if "base64" in content_type else bytearray(content, encoding='utf8')

        config_data = str(gzip.decompress(content_bytes), encoding='utf8') if "gz" in content_type else str(
            content_bytes, encoding='utf8')

        with open("connector.conf", "w") as file:
            print(config_data, file=file)

    def test_connect(self):
        hiro_api_handler = PasswordAuthTokenApiHandler(
            username=CONFIG.get('USERNAME'),
            password=CONFIG.get('PASSWORD'),
            client_id=CONFIG.get('CLIENT_ID'),
            client_secret=CONFIG.get('CLIENT_SECRET'),
            secure_logging=False,
            connection_handler=self.connection_handler
        )

        hiro_auth: HiroAuth = HiroAuth(api_handler=hiro_api_handler)

        print(json.dumps(hiro_auth.get_identity(), indent=2))

    def test_refresh_token(self):
        hiro_api_handler = PasswordAuthTokenApiHandler(
            username=CONFIG.get('USERNAME'),
            password=CONFIG.get('PASSWORD'),
            client_id=CONFIG.get('CLIENT_ID'),
            client_secret=CONFIG.get('CLIENT_SECRET'),
            secure_logging=False,
            connection_handler=self.connection_handler
        )

        handler = hiro_api_handler

        handler.get_token()
        handler.refresh_token()

        hiro_auth: HiroAuth = HiroAuth(api_handler=handler)

        print(json.dumps(hiro_auth.get_identity(), indent=2))

        handler.revoke_token()

        print(json.dumps(hiro_auth.get_identity(), indent=2))

    def test_auth_code_flow(self):
        hiro_api_handler = CodeFlowAuthTokenApiHandler(
            client_id=CONFIG.get('CLIENT_ID'),
            code='4b12c5f1-cdd7-3487-a5b0-82305b011b67',
            code_verifier='BQ3kyADe6RKYHttFwGPwvLrX_B6zwCr2vNRe00TQLfoRo-HYhUqM8sPKUQlkhbwUQxli2ZneFhFqx4xbltI4WQ',
            redirect_uri='http://wksw-whuebner.arago.de:8080/oauth2/app/callback.xhtml',
            secure_logging=False,
            connection_handler=self.connection_handler
        )

        hiro_api_handler.get_token()
        print(json.dumps(hiro_api_handler.decode_token(), indent=2))

        hiro_api_handler.refresh_token()
        print(json.dumps(hiro_api_handler.decode_token(), indent=2))

    def test_simple_query(self):
        # hiro_client: HiroGraph = HiroGraph(api_handler=self.hiro_api_handler)
        #
        # hiro_client.get_node(node_id="ckqjkt42s0fgf0883pf0cb0hx_ckqjl014l0hvr0883hxcvmcwq", meta=True)
        #
        # hiro_client: HiroGraph = HiroGraph(api_handler=self.hiro_api_handler2)
        #
        # hiro_client.get_node(node_id="ckqjkt42s0fgf0883pf0cb0hx_ckqjl014l0hvr0883hxcvmcwq", meta=True)
        #
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
        pass
