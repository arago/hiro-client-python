import concurrent.futures
import threading
import time

from hiro_graph_client.actionwebsocket import AbstractActionWebSocketHandler
from hiro_graph_client.clientlib import PasswordAuthTokenApiHandler, AbstractTokenApiHandler, SSLConfig
from .testconfig import CONFIG


def __init__(self, api_handler: AbstractTokenApiHandler):
    """ Initialize properties """
    super().__init__(api_handler)
    self._executor = None


class ActionWebSocket(AbstractActionWebSocketHandler):

    def __init__(self, api_handler: AbstractTokenApiHandler):
        """ Initialize properties """
        super().__init__(api_handler)
        self._executor = None

    def start(self) -> None:
        """ Initialize the executor """
        super().start()
        self._executor = concurrent.futures.ThreadPoolExecutor()

    def stop(self) -> None:
        """ Shut the executor down """
        if self._executor:
            self._executor.shutdown()
        self._executor = None
        super().stop()

    def handle_submit_action(self, action_id: str, capability: str, parameters: dict):
        """ Runs asynchronously in its own thread. """
        print(f"ID: {action_id}, Capability: {capability}, Parameters: {str(parameters)}")
        self.send_action_result(action_id, "Everything went fine.")

    def on_submit_action(self, action_id: str, capability: str, parameters: dict):
        """ Message *submitAction* has been received. Message is handled in thread executor. """
        if not self._executor:
            raise RuntimeError('ActionWebSocket has not been started.')
        self._executor.submit(ActionWebSocket.handle_submit_action, self, action_id, capability, parameters)

    def on_config_changed(self):
        """ The configuration of the ActionHandler has changed """
        pass


class TestActionWebsocket:
    api_handler = PasswordAuthTokenApiHandler(
        root_url=CONFIG.get('URL'),
        username=CONFIG.get('USERNAME'),
        password=CONFIG.get('PASSWORD'),
        client_id=CONFIG.get('CLIENT_ID'),
        client_secret=CONFIG.get('CLIENT_SECRET'),
        secure_logging=False,
        client_name="Test-client",
        ssl_config=SSLConfig(verify=False)
    )

    @staticmethod
    def wait_for_keypress(ws: ActionWebSocket):
        time.sleep(3)
        ws.stop()

    def test_actions(self):
        with ActionWebSocket(api_handler=self.api_handler) as ws:
            threading.Thread(daemon=True,
                             target=lambda _ws: TestActionWebsocket.wait_for_keypress(_ws),
                             args=(ws,)).start()
            ws.run_forever()
