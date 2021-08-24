# v4.3.0

* Adding SSL configuration

# v4.2.14

* Removed bug with reversed operator in websocketlib.
* Updated installation instructions in README.md.

# v4.2.13

* You need to explicitly set `query_params={'allscopes': 'true'}` if you
  want to enable it for EventWebSockets. If this is left out of the
  query_params, it will be added as 'allscopes': 'false'.
  
# v4.2.12

* Use typing to make sure, that `query_params=` for WebSockets is of type `Dict[str, str]`.
* Set `query_params={'allscopes': 'false'}` as default for the EventWebSocket.

# v4.2.11

* Debugged EventWebSocket handling.
* Abort connection when setting scope or filters failed.

# v4.2.10

* Adding scopes to EventWebSockets.

# v4.2.9

* Documentation of feature in v4.2.8

# v4.2.8

* WebSockets have new option `query_params` to add arbitrary query parameters to the initial websocket request.  

# v4.2.7

Changes to `AbstractAuthenticatedWebSocketHandler`:

* Introducing `run_forever()` which will return after the reader thread has been joined. This can happen when another
  thread calls `stop()` (normal exit) or an internal error occurs, either directly when the connection is attempted, a
  token got invalid and could not be refreshed, or any other exception that has been thrown in the internal reader
  thread.

  This ensures, that the main thread does not continue when the websocket reader thread is not there.

* Enable parallel executions of `send()` across multiple threads.

* Make sure, that only one thread triggers a restart by a call to `restart()`.

* Check for active websocket reader thread via `is_active()`.

* Update examples for websockets in README.md.

Generic

* Update README.md to show usage of `client_name`. 

# v4.2.6

* Do not require package uuid - it is already supplied with python

# v4.2.5

* Send valid close messages to backend.
* Introduced parameter `client_name` to give connections a name and also set header `User-Agent` more easily.

# v4.2.4

* Updated CHANGELOG.md.

# v4.2.3

* Hardening of clientlib. Removed some None-Value-Errors.

# v4.2.2

* Introduce parameter `remote_exit_codes` to `AbstractAuthenticatedWebSocketHandler`.

# v4.2.1

* Avoid blocking thread in `_backoff()` by not using `sleep()` but `threading.Condition.wait()`.

# v4.2.0

* Implement websocket protocols
    * event-ws
    * action-ws

# v4.1.3

* Use yield from instead of return

# v4.1.2

* Removed a bug with double yields on binary data

# v4.1.1

* Only log request/responses when logging.DEBUG is enabled

# v4.1.0

* Added timeseries handling to command `handle_vertices_combined`

# v4.0.0

* `AbstractTokenApiHandler`
    * Better token handling.
    * Resolve graph api endpoints via calling /api/version.
        * Ability to customize headers. Headers are handled case-insensitively and are submitted to requests
          capitalized.
        * Ability to override internal endpoints.


* AbstractIOCarrier works with `with` statements now.
* Added `BasicFileIOCarrier`.


* Removed `ApiConfig`.
* Renamed several internal classes.
* Better error messages.
* HTTP secure protocol logging.
* Fixed timestamp creation for tokens.


* Joe's suggestions - thanks Joe!

# v3.1.0

* Separation of APIs in client libraries. Currently, supported APIs are:
    * HiroGraph: https://core.arago.co/help/specs/?url=definitions/graph.yaml
    * HiroAuth: https://core.arago.co/help/specs/?url=definitions/auth.yaml
    * HiroApp: https://core.arago.co/help/specs/?url=definitions/app.yaml
* Use correct headers with binary transfers.
* Added gremlin and multi-id queries to HiroGraph.

# v3.0.0

* Renamed classes to match documentation elsewhere (i.e. Graphit -> HiroGraph, GraphitBatch -> HiroGraphBatch).
* Catch token expired error when refresh_token has expired.
* Documentation with examples

# v2.4.2

Added VERSION to package_data in setup.py

# v2.4.1

Added documentation for PyPI

# v2.4.0

Initial release after split from https://github.com/arago/hiro-clients

