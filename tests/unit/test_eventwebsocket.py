# from time import sleep

# from hiro_graph_client.clientlib import PasswordAuthTokenApiHandler, AbstractTokenApiHandler, accept_all_certs
# from hiro_graph_client.eventswebsocket import AbstractEventWebSocket, EventMessage, EventsFilter


# class EventWebSocket(AbstractEventWebSocket):
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


class TestEventWebsocket:
    # api_handler = PasswordAuthTokenApiHandler(
    #     root_url='',
    #     username='',
    #     password='',
    #     client_id='',
    #     client_secret='',
    #     secure_logging=False
    # )

    def test_events(self):
        # accept_all_certs()
        #
        # event_filter = EventsFilter(filter_id='testfilter', filter_content="(element.ogit/_type=ogit/MARS/Machine)")
        #
        # client = EventWebSocket(api_handler=self.api_handler, events_filters=[event_filter])
        # client.start_reader()
        # input("Press [Enter] to stop.")
        # # sleep(10)
        # client.close()

        pass
