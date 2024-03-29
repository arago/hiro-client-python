import threading
import time
from typing import List, Dict

from hiro_graph_client.clientlib import PasswordAuthTokenApiHandler, AbstractTokenApiHandler, SSLConfig
from hiro_graph_client.eventswebsocket import AbstractEventsWebSocketHandler, EventMessage, EventsFilter
from .testconfig import CONFIG


class EventsWebSocket(AbstractEventsWebSocketHandler):

    def __init__(self,
                 api_handler: AbstractTokenApiHandler,
                 events_filters: list,
                 scopes: List[str] = None,
                 query_params: Dict[str, str] = None):
        super().__init__(api_handler, events_filters, scopes, query_params)

    def on_create(self, message: EventMessage):
        print("Create:\n" + str(message))

    def on_update(self, message: EventMessage):
        print("Update:\n" + str(message))

    def on_delete(self, message: EventMessage):
        print("Delete:\n" + str(message))


class TestEventsWebsocket:
    api_handler = PasswordAuthTokenApiHandler(
        root_url=CONFIG.get('URL'),
        username=CONFIG.get('USERNAME'),
        password=CONFIG.get('PASSWORD'),
        client_id=CONFIG.get('CLIENT_ID'),
        client_secret=CONFIG.get('CLIENT_SECRET'),
        secure_logging=False,
        client_name="Test-Event-Websocket",
        ssl_config=SSLConfig(verify=False)
    )

    @staticmethod
    def wait_for_keypress(ws: EventsWebSocket):
        time.sleep(3)
        ws.stop()

    def test_events(self):
        events_filter = EventsFilter(filter_id='testfilter', filter_content="(element.ogit/_type=ogit/MARS/Machine)")

        with EventsWebSocket(api_handler=self.api_handler,
                             events_filters=[events_filter],
                             scopes=['ckqjksu370f4108834zpixcoi_ckqjkt42s0fgf0883pf0cb0hx'],
                             query_params={'delta': 'true'}) as ws:

            threading.Thread(daemon=True,
                             target=lambda _ws: TestEventsWebsocket.wait_for_keypress(_ws),
                             args=(ws,)).start()

            ws.run_forever()
