# from hiro_graph_client.clientlib import PasswordAuthTokenApiHandler, AbstractTokenApiHandler, accept_all_certs
from hiro_graph_client.eventswebsocket import AbstractEventsWebSocketHandler, EventMessage, EventsFilter


class EventsWebSocket(AbstractEventsWebSocketHandler):
    #
    #     def __init__(self, api_handler: AbstractTokenApiHandler, events_filters: list):
    #         super().__init__(api_handler, events_filters)
    #
    #     def on_create(self, message: EventMessage):
    #         print("Create:\n" + str(message))
    #
    #     def on_update(self, message: EventMessage):
    #         print("Update:\n" + str(message))
    #
    #     def on_delete(self, message: EventMessage):
    #         print("Delete:\n" + str(message))
    #
    #
    # class TestEventsWebsocket:
    #     api_handler = PasswordAuthTokenApiHandler(
    #         root_url="",
    #         username='',
    #         password='',
    #         client_id='',
    #         client_secret='',
    #         secure_logging=False
    #     )
    #
    def test_events(self):
        # accept_all_certs()
        #
        # events_filter = EventsFilter(filter_id='testfilter', filter_content="(element.ogit/_type=ogit/MARS/Machine)")
        #
        # with EventsWebSocket(api_handler=self.api_handler, events_filters=[events_filter]):
        #     input("Press [Enter] to stop.\n")
        #     # sleep(10)
        pass
