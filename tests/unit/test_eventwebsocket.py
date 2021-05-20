from hiro_graph_client.clientlib import PasswordAuthTokenApiHandler, AbstractTokenApiHandler, accept_all_certs
from hiro_graph_client.eventswebsocket import AbstractEventsWebSocketHandler, EventMessage, EventsFilter


class EventsWebSocket(AbstractEventsWebSocketHandler):

    def __init__(self, api_handler: AbstractTokenApiHandler, events_filters: list):
        super().__init__(api_handler, events_filters)

    def on_create(self, message: EventMessage):
        print("Create:\n" + str(message))

    def on_update(self, message: EventMessage):
        print("Update:\n" + str(message))

    def on_delete(self, message: EventMessage):
        print("Delete:\n" + str(message))


class TestEventsWebsocket:
    api_handler = PasswordAuthTokenApiHandler(
        root_url="https://ec2-52-213-82-23.eu-west-1.compute.amazonaws.com:8443",
        username='haas1000-connector-core',
        password='3m3vqmohgktqr74fde3ui984f9%1aZ',
        client_id='cju16o7cf0000mz77pbwbhl3q_ckm1z9o2m08km0781s2s7sqbr',
        client_secret='b7be95586cf54e5a2ec8ddda951e7dcb293173e451c41896244a0a47f00d950edd7288ce2cb6a324b22aaa4cdbae3d98cdcb3bfbac09a30c5c3f7ae663daf271',
        secure_logging=False
    )

    def test_events(self):
        accept_all_certs()

        events_filter = EventsFilter(filter_id='testfilter', filter_content="(element.ogit/_type=ogit/MARS/Machine)")

        with EventsWebSocket(api_handler=self.api_handler, events_filters=[events_filter]) as ws:
            input("Press [Enter] to stop.\n")
            # sleep(10)
