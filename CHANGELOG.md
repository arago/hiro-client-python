# v4.1.3

* Use yield from instead of return

# v4.1.2

* Removed bug with double yields on binary data

# v4.1.1

* Only log request/responses when logging.DEBUG is enabled

# v4.1.0

* Added timeseries handling to command `handle_vertices_combined`

# v4.0.0

* `AbstractTokenApiHandler`
  * Better token handling.
  * Resolve graph api endpoints via calling /api/version.
    * Ability to customize headers. Headers are handled 
      case-insensitively and are submitted to requests capitalized.
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

