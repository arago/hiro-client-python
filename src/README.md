# HIRO Graph API Client

This is a client library to access data of the [HIRO Graph](#graph-client-hirograph). It also allows uploads of huge
batches of data in parallel.

This library also contains classes for handling the [WebSockets](#websockets) `event-ws` and `action-ws` API.

__Status__

* Technical preview

For more information about HIRO Automation, look at https://www.arago.co/

For more information about the APIs this library covers, see https://developer.hiro.arago.co/7.0/api/ (Currently
implemented are `app`, `auth`, `graph`, `event-ws` and `action-ws` )

## Quickstart

To use this library, you will need an account at https://id.arago.co/ and access to an OAuth Client-Id and Client-Secret
to access the HIRO Graph. See also https://developer.hiro.arago.co.

Most of the documentation is done in the sourcecode.

### HiroGraph Example

Example to use the straightforward graph api client without any batch processing:

```python
from hiro_graph_client import PasswordAuthTokenApiHandler, HiroGraph

hiro_client: HiroGraph = HiroGraph(
    api_handler=PasswordAuthTokenApiHandler(
        root_url="https://core.arago.co",
        username='',
        password='',
        client_id='',
        client_secret=''
    )
)

# The commands of the Graph API are methods of the class HIROGraph.
# The next line executes a vertex query for instance. 
query_result = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"')

print(query_result)
```

### HiroGraphBatch Examples

#### Example 1

Example to use the batch client to process a batch of requests:

```python
from hiro_graph_client import PasswordAuthTokenApiHandler, HiroGraphBatch

hiro_batch_client: HiroGraphBatch = HiroGraphBatch(
    api_handler=PasswordAuthTokenApiHandler(
        root_url="https://core.arago.co",
        username='',
        password='',
        client_id='',
        client_secret=''
    )
)

# See code documentation about the possible commands and their attributes.
# For another variant of a valid data structure, see the example below.
commands: list = [
    {
        "handle_vertices": {
            "ogit/_xid": "haas1000:connector1:machine1"
        }
    },
    {
        "handle_vertices": {
            "ogit/_xid": "haas1000:connector2:machine2"
        }
    }
]

query_results: list = hiro_batch_client.multi_command(commands)

print(query_results)
```

#### Example 2

Example to use the batch client to process a batch of requests with callbacks for each result:

```python
from typing import Any, Iterator

from hiro_graph_client import AbstractTokenApiHandler, PasswordAuthTokenApiHandler, HiroGraphBatch, HiroResultCallback


class RunBatch(HiroResultCallback):
    hiro_batch_client: HiroGraphBatch

    def __init__(self, api_handler: AbstractTokenApiHandler):
        self.hiro_batch_client = HiroGraphBatch(
            callback=self,
            api_handler=api_handler)

    def result(self, data: Any, code: int) -> None:
        """
        This (abstract) method gets called for each command when results are available
        """
        print('Data: ' + str(data))
        print('Code: ' + str(code))

    def run(self, command_iter: Iterator[dict]):
        self.hiro_batch_client.multi_command(command_iter)


batch_runner: RunBatch = RunBatch(
    api_handler=PasswordAuthTokenApiHandler(
        root_url="https://core.arago.co",
        username='',
        password='',
        client_id='',
        client_secret=''
    )
)

# See code documentation about the possible commands and their attributes. This is a more compact notation of the
# same list of commands from the example above. Both variants are allowed.
commands: list = [
    {
        "handle_vertices": [
            {
                "ogit/_xid": "haas1000:connector1:machine1"
            },
            {
                "ogit/_xid": "haas1000:connector2:machine2"
            }
        ]
    }
]

batch_runner.run(commands)
```

## TokenApiHandler

Authorization against the HIRO Graph is done via tokens. These tokens are handled by classes of
type `AbstractTokenApiHandler` in this library. Each of the Hiro-Client-Object (`HiroGraph`, `HiroGraphBatch`
, `HiroApp`, etc.) need to have some kind of TokenApiHandler at construction.

This TokenApiHandler is also responsible to determine the most up-to-date endpoints for the API calls. You can supply a
custom list of endpoints by using the dict parameter `custom_endpoints=` on construction.

A custom list of headers can also be set via the dict parameter `headers=` in the constructor. These would update the
internal headers. Header names can be supplied in any upper/lower-case.

This library supplies the following TokenApiHandlers:

---

### FixedTokenApiHandler

A simple TokenApiHandler that is generated with a preset-token at construction. Cannot update its token.

---

### EnvironmentTokenApiHandler

A TokenApiHandler that reads an environment variable (default is `HIRO_TOKEN`) from the runtime environment. Will only
update its token when the environment variable changes externally.

---

### PasswordAuthTokenApiHandler

This TokenApiHandler logs into the HiroAuth backend and obtains a token from login credentials. This is also the only
TokenApiHandler (so far) that automatically tries to renew a token from the backend when it has expired.

---

All code examples in this documentation can use these TokenApiHandlers interchangeably, depending on how such a token is
provided.

The HiroGraph example from above with another customized TokenApiHandler:

```python
from hiro_graph_client import EnvironmentTokenApiHandler, HiroGraph

hiro_client: HiroGraph = HiroGraph(
    api_handler=EnvironmentTokenApiHandler(
        root_url="https://core.arago.co"
    )
)

# The commands of the Graph API are methods of the class HIROGraph.
# The next line executes a vertex query for instance. 
query_result = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"')

print(query_result)
```

Example with additional parameters:

```python
from hiro_graph_client import EnvironmentTokenApiHandler, HiroGraph

hiro_client: HiroGraph = HiroGraph(
    api_handler=EnvironmentTokenApiHandler(
        root_url="https://core.arago.co",
        env_var='_TOKEN',
        headers={
            'X-Custom-Header': 'My custom value'
        },
        custom_endpoints={
            "graph": "/api/graph/7.2",
            "auth": "/api/auth/6.2"
        },
        client_name="HiroGraph (testing)"  # Will be used in the header 'User-Agent'
    )
)

# The commands of the Graph API are methods of the class HIROGraph.
# The next line executes a vertex query for instance. 
query_result = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"')

print(query_result)
```

## Handler sharing

When you need to access multiple APIs, it is a good idea to share the TokenApiHandler between them. This avoids
unnecessary api version requests and unnecessary token requests with the PasswordAuthTokenApiHandler for instance.

```python
from hiro_graph_client import HiroGraph, HiroGraphBatch, HiroApp, PasswordAuthTokenApiHandler

hiro_api_handler = PasswordAuthTokenApiHandler(
    root_url="https://core.arago.co",
    username='',
    password='',
    client_id='',
    client_secret=''
)

hiro_client: HiroGraph = HiroGraph(
    api_handler=hiro_api_handler
)

hiro_batch_client: HiroGraphBatch = HiroGraphBatch(
    api_handler=hiro_api_handler
)

hiro_app_client: HiroApp = HiroApp(
    api_handler=hiro_api_handler
)
```

## SSL Configuration

SSL parameters are configured using the class `SSLConfig`. This class translates the parameters given to the required
fields for the `requests` library of Python (parameters `cert` and `verify` there). This configuration is given to the
TokenApiHandlers and will be used by the clients attached to it as well.

If this is not set, the default settings of the library `requests` will be used, which is to verify any server certificates by using system defaults.

#### Example: Disable verification

```python
from hiro_graph_client import EnvironmentTokenApiHandler, HiroGraph, SSLConfig

hiro_client: HiroGraph = HiroGraph(
    api_handler=EnvironmentTokenApiHandler(
        root_url="https://core.arago.co",
        # Disable any verification.
        ssl_config=SSLConfig(verify=False)
    )
)

query_result = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"')

print(query_result)
```

#### Example: Set custom SSL certificates

```python
from hiro_graph_client import EnvironmentTokenApiHandler, HiroGraph, SSLConfig

hiro_client: HiroGraph = HiroGraph(
    api_handler=EnvironmentTokenApiHandler(
        root_url="https://core.arago.co",
        # Set custom certification files. If any of them are omitted, system defaults will be used.
        ssl_config=SSLConfig(
            cert_file="<path to client certificate file>",
            key_file="<path to key file for the client certificate>",
            ca_bundle_file="<path to the ca_bundle to verify the server certificate>"
        )
    )
)

query_result = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"')

print(query_result)
```

## Graph Client "HiroGraph"

The Graph Client is mostly straightforward to use, since all public methods of this class represent an API call in the
[Graph API](https://core.arago.co/help/specs/?url=definitions/graph.yaml). Documentation is available in source code as
well. Some calls are a bit more complicated though and explained in more detail below:

### Attachments

Attachments are only available with vertices of type `ogit/_type: "ogit/Attachment"`.

To upload data to such a vertex, use `HiroGraph.post_attachment(data=...)`. The parameter `data=` will be given directly
to the call of the Python library `requests` as  `requests.post(data=...)`. To stream data, set `data` to an object of
type `IO`. See the documentation of the Python library `requests` for more details.

Downloading an attachment is done in chunks, so huge blobs of data in memory can be avoided when streaming this data.
Each chunk is 64k by default.

To stream such an attachment to a file, see the example below:

```python
ogit_id = '<ogit/_id of a vertex of type ogit/_type:"ogit/Attachment">'
data_iter = hiro_client.get_attachment(ogit_id)

with io.start("attachment.bin", "wb") as file:
    for chunk in data_iter:
        file.write(chunk)
```

To read the complete data in memory, see this example:

```python
ogit_id = '<ogit/_id of a vertex of type ogit/_type:"ogit/Attachment">'
data_iter = hiro_client.get_attachment(ogit_id)

attachment = b''.join(data_iter)
```

## Batch Client "HiroGraphBatch"

It is recommended to use the included HiroGraphBatch client when uploading large quantities of data into the HIRO Graph.
This client handles parallel upload of data and makes creating vertices with their edges and attachments easier.

The HiroGraphBatch expects a list of commands with their respective attribute payload as input. The method to run such a
batch is always `HiroGraphBatch.multi_command`.

See examples from [HiroGraphBatch](#hirographbatch) above.

### Input data format

The data format for input of `HiroGraphBatch.multi_command` is a list. This method iterates over this list and treats
each dict it finds as a key-value-pair with the name of a command as key and either a single dict of attributes, or a
list of multiple attribute dicts as value(s) for this command.

These commands are run in parallel across up to eight threads by default, so their order is likely to change in the
results. Commands given in these command lists should therefore never depend on each other. See the documentation on the
constructor `HiroGraphBatch.__init__` for more information.

The following two (bad!) examples are equivalent:

```python
commands: list = [
    {
        "create_vertices": {
            "ogit/_xid": "haas1000:connector1:machine1"
        }
    },
    {
        "handle_vertices": {
            "ogit/_xid": "haas1000:connector2:machine2"
        }
    },
    {
        "handle_vertices": {
            "ogit/_xid": "haas1000:connector3:machine3"
        }
    },
    {
        "delete_vertices": {
            "ogit/_xid": "haas1000:connector1:machine1"
        }
    },
    {
        "delete_vertices": {
            "ogit/_xid": "haas1000:connector2:machine2"
        }
    },
    {
        "delete_vertices": {
            "ogit/_xid": "haas1000:connector3:machine3"
        }
    }
]
```

```python
commands: list = [
    {
        "create_vertices": [
            {
                "ogit/_xid": "haas1000:connector1:machine1"
            }
        ],
        "handle_vertices": [
            {
                "ogit/_xid": "haas1000:connector2:machine2"
            },
            {
                "ogit/_xid": "haas1000:connector3:machine3"
            }
        ],
        "delete_vertices": [
            {
                "ogit/_xid": "haas1000:connector1:machine1"
            },
            {
                "ogit/_xid": "haas1000:connector2:machine2"
            },
            {
                "ogit/_xid": "haas1000:connector3:machine3"
            }
        ]
    }
]
```

These examples are bad, because delete_vertices depends on create/handle_vertices (there has to be a vertex first before
it can be deleted). You should call `HiroGraphBatch.multi_command` twice in this case:

```python
commands1: list = [
    {
        "create_vertices": [
            {
                "ogit/_xid": "haas1000:connector1:machine1"
            }
        ],
        "handle_vertices": [
            {
                "ogit/_xid": "haas1000:connector2:machine2"
            },
            {
                "ogit/_xid": "haas1000:connector3:machine3"
            }
        ]
    }
]

commands2: list = [
    {
        "delete_vertices": [
            {
                "ogit/_xid": "haas1000:connector1:machine1"
            },
            {
                "ogit/_xid": "haas1000:connector2:machine2"
            },
            {
                "ogit/_xid": "haas1000:connector3:machine3"
            }
        ]
    }
]

query_results = []

query_results.extend(hiro_batch_client.multi_command(commands1))
query_results.extend(hiro_batch_client.multi_command(commands2))
```

#### IOCarrier

When uploading attachments into the HIRO Graph, it is best practice streaming that data when possible. To avoid having
many open IO connections when uploading many files for instance, children of the class `AbstractIOCarrier` can be
implemented and used. Children that derive from this class open their IO just before the upload and close it immediately
afterwards.

This library provides a class `BasicFileIOCarrier` for file operations.

See [Example for add_attachments](#add_attachments).

### Result data format

Result values contain dicts that carry all information about the executed commands. The order of the results is
independent of the order in which the input data has been submitted.

One dict has the following structure:

```python
result: dict = {
    "status": "success|fail",
    "entity": "vertex|edge|timeseries|attachment|undefined",
    "action": "create|update|delete|undefined",
    "data": {
        "<On success>": "<Data of the result of the command.>",
        "<On fail>": "<Dict with a copy of the original data of the command.>"
    }
}
```

These dicts are collected in a list when no callback is configured, see [Example 1](#example-1), or given back in the
callback method as `data`, see [Example 2](#example-2).

Example of a list result:

```python
query_results: list = [
    {
        "status": "success",
        "entity": "vertex",
        "action": "create",
        "data": {
            "ogit/_created-on": 1601030883647,
            "ogit/_xid": "machine4",
            "ogit/_organization": "ckeckyxi60c8k0619otx9i5tq_ckeckyxi60c8o0619fsizblds",
            "/admin_contact": "info@admin.co",
            "ogit/name": "machine 4",
            "ogit/_modified-on": 1601030883647,
            "ogit/_id": "ckeckz5un0chl0619fyskvn2a_ckfi4g85b8vak06191dxpaqn0",
            "ogit/_creator": "ckeckyxi60c8k0619otx9i5tq_ckeckzivg0d2f0619o3guv8o1",
            "ogit/MARS/Machine/class": "Linux",
            "ogit/_graphtype": "vertex",
            "ogit/_owner": "ckeckyxi60c8k0619otx9i5tq_ckeckyxi60c8m061999q77xdb",
            "ogit/_v-id": "1601030883647-9oRXX8",
            "ogit/_v": 1,
            "ogit/MARS/Machine/ram": "2G",
            "ogit/_modified-by-app": "cju16o7cf0000mz77pbwbhl3q_ckecksfda040q06190ygwv4jz",
            "ogit/_is-deleted": false,
            "ogit/_creator-app": "cju16o7cf0000mz77pbwbhl3q_ckecksfda040q06190ygwv4jz",
            "ogit/_modified-by": "ckeckyxi60c8k0619otx9i5tq_ckeckzivg0d2f0619o3guv8o1",
            "ogit/_scope": "ckeckyxi60c8k0619otx9i5tq_ckeckz5un0chl0619fyskvn2a",
            "ogit/_type": "ogit/MARS/Machine"
        }
    },
    {
        "status": "success",
        "entity": "vertex",
        "action": "create",
        "data": {
            "ogit/_created-on": 1601030883847,
            "ogit/_xid": "machine5",
            "ogit/_organization": "ckeckyxi60c8k0619otx9i5tq_ckeckyxi60c8o0619fsizblds",
            "/admin_contact": "contact@admin.co",
            "ogit/name": "machine 5",
            "ogit/_modified-on": 1601030883847,
            "ogit/_id": "ckeckz5un0chl0619fyskvn2a_ckfi4g8av8vap0619okulfydq",
            "ogit/_creator": "ckeckyxi60c8k0619otx9i5tq_ckeckzivg0d2f0619o3guv8o1",
            "ogit/MARS/Machine/class": "Linux",
            "ogit/_graphtype": "vertex",
            "ogit/_owner": "ckeckyxi60c8k0619otx9i5tq_ckeckyxi60c8m061999q77xdb",
            "ogit/_v-id": "1601030883847-3TyBFf",
            "ogit/_v": 1,
            "ogit/MARS/Machine/ram": "4G",
            "ogit/_modified-by-app": "cju16o7cf0000mz77pbwbhl3q_ckecksfda040q06190ygwv4jz",
            "ogit/_is-deleted": false,
            "ogit/_creator-app": "cju16o7cf0000mz77pbwbhl3q_ckecksfda040q06190ygwv4jz",
            "ogit/_modified-by": "ckeckyxi60c8k0619otx9i5tq_ckeckzivg0d2f0619o3guv8o1",
            "ogit/_scope": "ckeckyxi60c8k0619otx9i5tq_ckeckz5un0chl0619fyskvn2a",
            "ogit/_type": "ogit/MARS/Machine"
        }
    },
    {
        "status": "fail",
        "entity": "vertex",
        "action": "create",
        "data": {
            "error": "HTTPError",
            "code": 500,
            "message": "500 Internal Server Error: Unspecified exception.",
            "original_data": {
                "ogit/_xid": "machine6",
                "ogit/_type": "ogit/MARS/Machine",
                "ogit/MARS/Machine/class": "Linux",
                "ogit/name": "machine 5A",
                "ogit/MARS/Machine/ram": "8G",
                "/admin_contact": "info@admin.co"
            }
        }
    },
    {
        "status": "fail",
        "entity": "vertex",
        "action": "create",
        "data": {
            "error": "HTTPError",
            "code": 500,
            "message": "500 Internal Server Error: Unspecified exception.",
            "original_data": {
                "ogit/_xid": "machine7",
                "ogit/_type": "ogit/MARS/Machine",
                "ogit/MARS/Machine/class": "Linux",
                "ogit/name": "machine 4A",
                "ogit/MARS/Machine/ram": "4G",
                "/admin_contact": "contact@admin.co"
            }
        }
    }
]
```

### Commands

The following command keywords for the commands list structure are implemented in the HiroGraphBatch client:

---

#### create_vertices

Create a batch of vertices via
https://core.arago.co/help/specs/?url=definitions/graph.yaml#/[Graph]_Entity/post_new__type_

* `ogit/_type` must be present in each of the attribute dicts.

* Attribute keys that start with `=`, `+` or `-` denote map value entries. These values have to be in the correct format
  according to https://developer.hiro.arago.co/7.0/documentation/api/list-api/.

* Attributes of the format `"xid:[attribute_name]": "[ogit/_xid]"` are resolved to `"[attribute_name]": "[ogit/_id]"` by
  querying HIRO before executing the main command.

  This can be especially handy when creating issues:

  An attribute in the form `"xid:ogit/Automation/originNode": "ogit:xid:of:the:desired:vertex"` would resolve this
  attribute to `"ogit/Automation/originNode": "ogitidofthedesiredvertex1_abcdefghijklmnopqrstuvw12"` in the issue vertex
  to create.

Example payload for four new vertices:

```python
commands: list = [
    {
        "create_vertices": [
            {
                "ogit/_xid": "machine4",
                "ogit/_type": "ogit/MARS/Machine",
                "ogit/MARS/Machine/class": "Linux",
                "ogit/name": "machine 4",
                "ogit/MARS/Machine/ram": "2G",
                "/admin_contact": "info@admin.co"
            },
            {
                "ogit/_xid": "machine5",
                "ogit/_type": "ogit/MARS/Machine",
                "ogit/MARS/Machine/class": "Linux",
                "ogit/name": "machine 5",
                "ogit/MARS/Machine/ram": "4G",
                "/admin_contact": "contact@admin.co"
            },
            {
                "ogit/_xid": "machine6",
                "ogit/_type": "ogit/MARS/Machine",
                "ogit/MARS/Machine/class": "Linux",
                "ogit/name": "machine 5A",
                "ogit/MARS/Machine/ram": "8G",
                "/admin_contact": "info@admin.co"
            },
            {
                "ogit/_xid": "machine7",
                "ogit/_type": "ogit/MARS/Machine",
                "ogit/MARS/Machine/class": "Linux",
                "ogit/name": "machine 4A",
                "ogit/MARS/Machine/ram": "4G",
                "/admin_contact": "contact@admin.co"
            }
        ]
    }
]
```

---

#### update_vertices

Update a batch of vertices via
https://core.arago.co/help/specs/?url=definitions/graph.yaml#/[Graph]_Entity/post__id_

* Either `ogit/_id` or `ogit/_xid` must be present in each of the attribute dicts.

* Attribute keys that start with `=`, `+` or `-` denote map value entries. These values have to be in the correct format
  according to https://developer.hiro.arago.co/7.0/documentation/api/list-api/.

* Attributes of the format `"xid:[attribute_name]": "[ogit/_xid]"` are resolved to `"[attribute_name]": "[ogit/_id]"` by
  querying HIRO before executing the main command.

Example payload to update four vertices:

```python
commands: list = [
    {
        "update_vertices": [
            {
                "ogit/_xid": "machine4",
                "ogit/name": "machine one",
                "ogit/MARS/Machine/ram": "4G"
            },
            {
                "ogit/_xid": "machine5",
                "ogit/name": "machine two",
                "ogit/MARS/Machine/ram": "16G"
            },
            {
                "ogit/_xid": "machine6",
                "ogit/name": "machine three",
                "ogit/MARS/Machine/ram": "16G",
                "/admin_contact": None
            },
            {
                "ogit/_id": "cju16o7cf0000mz77pbwbhf8d_ckm1z9o2m08km0781s2s7abce",
                "ogit/MARS/Machine/class": "Linux",
                "ogit/name": "machine three backup",
                "ogit/MARS/Machine/ram": "8G"
            }
        ]
    }
]
```

`"/admin_contact": None` from above would remove this attribute from the found vertex.

---

#### handle_vertices

Create or update a batch of vertices depending on the data provided in their attributes.

If the attributes for a vertex definition contain `ogit/_id` or `ogit/_xid`, an existing vertex will be updated when it
can be found. If these attributes are missing or no such vertex can be found but `ogit/_type` is given, a new vertex of
this type will be created.

The data structures are the same as in [create_vertices](#create_vertices) and [update_vertices](#update_vertices)
above.

Example:

```python
commands: list = [
    {
        "handle_vertices": [
            {
                "ogit/_xid": "machine4",
                "ogit/name": "machine one",
                "ogit/MARS/Machine/ram": "4G"
            },
            {
                "ogit/_xid": "machine5",
                "ogit/_type": "ogit/MARS/Machine",
                "ogit/name": "machine two",
                "ogit/MARS/Machine/ram": "16G"
            },
            {
                "ogit/_xid": "machine6",
                "ogit/name": "machine three",
                "ogit/MARS/Machine/ram": "16G",
                "/admin_contact": None
            },
            {
                "ogit/_id": "cju16o7cf0000mz77pbwbhf8d_ckm1z9o2m08km0781s2s7abce",
                "ogit/MARS/Machine/class": "Linux",
                "ogit/name": "machine three backup",
                "ogit/MARS/Machine/ram": "8G"
            }
        ]
    }
]
```

`"/admin_contact": None` from above would remove this attribute from the found vertex.

---

#### handle_vertices_combined

Same as [handle_vertices](#handle_vertices) above, but also collect additional information about edge connections,
timeseries and data attachments that might be given in their attributes.

The execution of this command has two stages:

1) Use the vertex attributes and execute [handle_vertices](#handle_vertices) on _all_ vertices given, ignoring all
   attributes that start with `_`. Store the `ogit/_id`s of the handled vertices for stage two.
2) When stage one is finished, take those remaining attributes, reformat them if necessary and
   execute [create_edges](#create_edges),   [add_timeseries](#add_timeseries) or [add_attachments](#add_attachments)
   with them, using the `ogit/_id`s of the associated vertices from stage one.

Each stage executes its activities in parallel, so what has been written about dependencies
at [Input Data Format](#input-data-format) still applies for each stage.

The following additional attributes are supported:

* Edge attributes are given as a list with a key `_edge_data`. This list contains dicts with the following attributes:
    * `verb`: (required) Verb for that edge for the vertex of the current row.
    * `direction`: ("in"/"out") from the view of the current vertex. "in" points towards, "out"
      points away from the current vertex. Default is "out" if this key is missing.
    * One of the following keys is required to find the vertex to connect to:
        * `vertex_id`: ogit/_id of the other vertex.
        * `vertex_xid`: ogit/_xid of the other vertex.

  See also [create_edges](#create_edges), but take note, that the structure of `_edge_data` is reformatted internally to
  match the data needed for create_edges.


* Timeseries attributes are given as a list with a key `_timeseries_data`. This list contains dicts of
    * `timestamp` for epoch in ms.
    * `value` for the timeseries value.

  See also [add_timeseries](#add_timeseries), but take note, that the key of the list is called just `items` there.


* Content attributes are given as a dict with a key `_content_data` which contains:
    * `data`: Content to upload. This can be anything the Python library `requests` supports as attribute `data=`
      in  `requests.post(data=...)`. If you set an IO object as data, it will be streamed. Also take a look at the
      class `AbstractIOCarrier` to transparently handle opening and closing of IO sources - see [IOCarrier](#iocarrier).
    * `mimetype`: (optional) Content-Type of the content.

  See also [add_attachments](#add_attachments)

General structure:

```python
commands: list = [
    {
        "handle_vertices_combined": [
            {
                "<vertex attribute>": "<some value>",
                "_edge_data": {
                },
                "_timeseries_data": {
                },
                "_content_data": {
                }
            }
        ]
    }
]
```

Example for edge data:

```python
commands: list = [
    {
        "handle_vertices_combined": [
            {
                "ogit/_xid": "crew:NCC-1701-D:picard",
                "ogit/_type": "ogit/Forum/Profile",
                "ogit/name": "Jean-Luc Picard",
                "ogit/Forum/username": "Picard",
                "_edge_data": [
                    {
                        "verb": "ogit/Forum/mentions",
                        "direction": "out",
                        "vertex_xid": "crew:NCC-1701-D:data"
                    },
                    {
                        "verb": "ogit/Forum/mentions",
                        "direction": "out",
                        "vertex_xid": "crew:NCC-1701-D:worf"
                    }
                ]
            },
            {
                "ogit/_xid": "crew:NCC-1701-D:worf",
                "ogit/_type": "ogit/Forum/Profile",
                "ogit/name": "Worf",
                "ogit/Forum/username": "Worf",
                "_edge_data": [
                    {
                        "verb": "ogit/subscribes",
                        "direction": "out",
                        "vertex_xid": "crew:NCC-1701-D:picard"
                    }
                ]
            },
            {
                "ogit/_xid": "crew:NCC-1701-D:data",
                "ogit/_type": "ogit/Forum/Profile",
                "ogit/name": "Data",
                "ogit/Forum/username": "Data",
                "_edge_data": [
                    {
                        "verb": "ogit/Forum/mentions",
                        "direction": "out",
                        "vertex_xid": "crew:NCC-1701-D:worf"
                    },
                    {
                        "verb": "ogit/subscribes",
                        "direction": "in",
                        "vertex_xid": "crew:NCC-1701-D:worf"
                    }
                ]
            }
        ]
    }
]
```

Example for timeseries data:

```python
commands: list = [
    {
        "handle_vertices_combined": [
            {
                "ogit/_xid": "crew:NCC-1701-D:picard",
                "ogit/_type": "ogit/Forum/Profile",
                "ogit/name": "Jean-Luc Picard",
                "ogit/Forum/username": "Picard",
                "_timeseries_data": [
                    {
                        "timestamp": "1440035678000",
                        "value": "Sighs"
                    },
                    {
                        "timestamp": "1440035944000",
                        "value": "Make it so!"
                    }
                ]
            },
            {
                "ogit/_xid": "crew:NCC-1701-D:worf",
                "ogit/_type": "ogit/Forum/Profile",
                "ogit/name": "Worf",
                "ogit/Forum/username": "Worf",
                "_timeseries_data": [
                    {
                        "timestamp": "1440035678000",
                        "value": "Grunts"
                    },
                    {
                        "timestamp": "1440035944000",
                        "value": "Aye captain"
                    }
                ]
            }
        ]
    }
]
```

Example for attachment data:

```python
commands: list = [
    {
        "handle_vertices_combined": [
            {
                "ogit/_xid": "attachment:arago:test:0:lorem-ipsum",
                "ogit/_type": "ogit/Attachment",
                "ogit/name": "test text",
                "ogit/type": "text",
                "_content_data": {
                    "mimetype": "text/plain",
                    "data": "Auch gibt es niemanden, der den Schmerz an sich liebt, sucht oder wünscht, nur, weil er Schmerz ist, es sei denn, es kommt zu zufälligen Umständen, in denen Mühen und Schmerz ihm große Freude bereiten können.\n\nUm ein triviales Beispiel zu nehmen, wer von uns unterzieht sich je anstrengender körperlicher Betätigung, außer um Vorteile daraus zu ziehen? Aber wer hat irgend ein Recht, einen Menschen zu tadeln, der die Entscheidung trifft, eine Freude zu genießen, die keine unangenehmen Folgen hat, oder einen, der Schmerz vermeidet, welcher keine daraus resultierende Freude nach sich zieht? Auch gibt es niemanden, der den Schmerz"
                }
            },
            {
                "ogit/_xid": "attachment:arago:test:1:lorem-ipsum",
                "ogit/_type": "ogit/Attachment",
                "ogit/name": "text text from IO",
                "ogit/type": "text",
                "_content_data": {
                    "mimetype": "text/plain",
                    "data": BasicFileIOCarrier('<filename>')
                }
            }
        ]
    }
]
```

---

#### delete_vertices

Delete a batch of vertices via
https://core.arago.co/help/specs/?url=definitions/graph.yaml#/[Graph]_Entity/delete__id_

Either `ogit/_id` or `ogit/_xid` must be present in each of the attribute dicts.

Example to delete four vertices:

```python
commands: list = [
    {
        "delete_vertices": [
            {
                "ogit/_xid": "machine4"
            },
            {
                "ogit/_xid": "machine5"
            },
            {
                "ogit/_xid": "machine6"
            },
            {
                "ogit/_id": "cju16o7cf0000mz77pbwbhf8d_ckm1z9o2m08km0781s2s7abce"
            }
        ]
    }
]
```

---

#### create_edges

Connect vertices via
https://core.arago.co/help/specs/?url=definitions/graph.yaml#/[Graph]_Verb/post_connect__type_

Each attribute dict needs the following keys:

* `from:ogit/_id` or `from:ogit/_xid`
* `verb`: The ogit verb for the edge
* `to:ogit/_id` or `to:ogit/_xid`

Example:

```python
commands: list = [
    {
        "create_edges": [
            {
                "from:ogit/_xid": "crew:NCC-1701-D:worf",
                "verb": "ogit/subscribes",
                "to:ogit/_xid": "crew:NCC-1701-D:picard"
            },
            {
                "from:ogit/_xid": "crew:NCC-1701-D:worf",
                "verb": "ogit/subscribes",
                "to:ogit/_xid": "crew:NCC-1701-D:data"
            },
            {
                "from:ogit/_xid": "crew:NCC-1701-D:picard",
                "verb": "ogit/Forum/mentions",
                "to:ogit/_xid": "crew:NCC-1701-D:data"
            },
            {
                "from:ogit/_xid": "crew:NCC-1701-D:picard",
                "verb": "ogit/Forum/mentions",
                "to:ogit/_xid": "crew:NCC-1701-D:worf"
            },
            {
                "from:ogit/_xid": "crew:NCC-1701-D:data",
                "verb": "ogit/Forum/mentions",
                "to:ogit/_xid": "crew:NCC-1701-D:worf"
            }
        ]
    }
]
```

---

#### delete_edges

Delete connections between vertices via
https://core.arago.co/help/specs/?url=definitions/graph.yaml#/[Graph]_Verb/delete__id_

The data structure of the payload is the same as with [create_edges](#create_edges).

Example:

```python
commands: list = [
    {
        "delete_edges": [
            {
                "from:ogit/_xid": "crew:NCC-1701-D:worf",
                "verb": "ogit/subscribes",
                "to:ogit/_xid": "crew:NCC-1701-D:picard"
            },
            {
                "from:ogit/_xid": "crew:NCC-1701-D:worf",
                "verb": "ogit/subscribes",
                "to:ogit/_xid": "crew:NCC-1701-D:data"
            },
            {
                "from:ogit/_xid": "crew:NCC-1701-D:picard",
                "verb": "ogit/Forum/mentions",
                "to:ogit/_xid": "crew:NCC-1701-D:data"
            },
            {
                "from:ogit/_xid": "crew:NCC-1701-D:picard",
                "verb": "ogit/Forum/mentions",
                "to:ogit/_xid": "crew:NCC-1701-D:worf"
            },
            {
                "from:ogit/_xid": "crew:NCC-1701-D:data",
                "verb": "ogit/Forum/mentions",
                "to:ogit/_xid": "crew:NCC-1701-D:worf"
            }
        ]
    }
]
```

---

#### add_timeseries

Add timeseries data to a vertex with "ogit/_type" of "ogit/Timeseries" via
https://core.arago.co/help/specs/?url=definitions/graph.yaml#/[Storage]_Timeseries/post__id__values

Each attribute dict needs the following keys:

* `ogit/_id` or `ogit/_xid` with valid ids for vertices.
* `items` a list of timeseries items for this vertex, containing dicts of:
    * `timestamp` for epoch in ms.
    * `value` for the timeseries value.

Example:

```python
commands: list = [
    {
        "add_timeseries": [
            {
                "ogit/_xid": "machine4",
                "items": [
                    {
                        "timestamp": "1440035678000",
                        "value": "Value 4A"
                    },
                    {
                        "timestamp": "1440035944000",
                        "value": "Value 4B"
                    }
                ]
            },
            {
                "ogit/_xid": "machine5",
                "items": [
                    {
                        "timestamp": "1440035678000",
                        "value": "Value 5A"
                    },
                    {
                        "timestamp": "1440035944000",
                        "value": "Value 5B"
                    }
                ]
            }
        ]
    }
]
```

---

#### add_attachments

Add binary data to a vertex with "ogit/_type" of "ogit/Attachment" by using
https://core.arago.co/help/specs/?url=definitions/graph.yaml#/[Storage]_Blob/post__id__content

* `ogit/_id`or `ogit/_xid`
* `_content_data`: A dict with the following keys:
    * `data`: Content to upload. This can be anything the Python library `requests` supports as attribute `data=`
      in  `requests.post(data=...)`. If you set an IO object as data, it will be streamed. Also take a look at the
      class `AbstractIOCarrier` to transparently handle opening and closing of IO sources - see [IOCarrier](#iocarrier).
    * `mimetype`: (optional) Content-Type of the content.

Example:

```python
commands: list = [
    {
        "add_attachments": [
            {
                "ogit/_xid": "attachment:arago:test:0:lorem-ipsum",
                "_content_data": {
                    "mimetype": "text/plain",
                    "data": "Auch gibt es niemanden, der den Schmerz an sich liebt, sucht oder wünscht, nur, weil er Schmerz ist, es sei denn, es kommt zu zufälligen Umständen, in denen Mühen und Schmerz ihm große Freude bereiten können.\n\nUm ein triviales Beispiel zu nehmen, wer von uns unterzieht sich je anstrengender körperlicher Betätigung, außer um Vorteile daraus zu ziehen? Aber wer hat irgend ein Recht, einen Menschen zu tadeln, der die Entscheidung trifft, eine Freude zu genießen, die keine unangenehmen Folgen hat, oder einen, der Schmerz vermeidet, welcher keine daraus resultierende Freude nach sich zieht? Auch gibt es niemanden, der den Schmerz"
                }
            },
            {
                "ogit/_xid": "attachment:arago:test:1:lorem-ipsum",
                "_content_data": {
                    "mimetype": "text/plain",
                    "data": BasicFileIOCarrier('<filename>')
                }
            }
        ]
    }
]
```

---

## WebSockets

This library contains classes that make using HIRO WebSocket protocols easier. They handle authentication, exceptions
and much more.

The classes do not handle buffering of messages, so it is the duty of the programmer to ensure, that incoming messages
are either handled quickly or being buffered to avoid clogging the websocket. The classes are thread-safe, so it is
possible to handle each incoming message asynchronously in its own thread and have those threads send results back if
needed (See multithreaded example in [Action WebSocket](#action-websocket)).

### Event WebSocket

This websocket receives notifications about changes to vertices that match a certain filter.

See also [API description of event-ws](https://core.arago.co/help/specs/?url=definitions/events-ws.yaml)

Example:

```python
import threading
import concurrent.futures

from hiro_graph_client.clientlib import FixedTokenApiHandler
from hiro_graph_client.eventswebsocket import AbstractEventsWebSocketHandler, EventMessage, EventsFilter


class EventsWebSocket(AbstractEventsWebSocketHandler):

    def on_create(self, message: EventMessage):
        """ Vertex has been created """
        print("Create:\n" + str(message))

    def on_update(self, message: EventMessage):
        """ Vertex has been updated """
        print("Update:\n" + str(message))

    def on_delete(self, message: EventMessage):
        """ Vertex has been removed """
        print("Delete:\n" + str(message))


def wait_for_keypress(websocket: EventsWebSocket):
    input("Press [Enter] to stop.\n")
    websocket.stop()


events_filter = EventsFilter(filter_id='testfilter', filter_content="(element.ogit/_type=ogit/MARS/Machine)")

with EventsWebSocket(api_handler=FixedTokenApiHandler('HIRO_TOKEN'),
                     events_filters=[events_filter],
                     scopes=[],
                     query_params={"allscopes": "true", "delta": "false"}) as ws:
    threading.Thread(daemon=True, target=wait_for_keypress, args=(ws,)).start()
    ws.run_forever()

```

### Action WebSocket

This websocket receives notifications about actions that have been triggered within a KI. Use this to write your own
custom action handler.

See also [API description of action-ws](https://core.arago.co/help/specs/?url=definitions/action-ws.yaml)

Simple example:

```python
import threading

from hiro_graph_client.actionwebsocket import AbstractActionWebSocketHandler
from hiro_graph_client.clientlib import FixedTokenApiHandler


class ActionWebSocket(AbstractActionWebSocketHandler):

    def on_submit_action(self, action_id: str, capability: str, parameters: dict):
        """ Message *submitAction* has been received """

        # Handle the message
        print(f"ID: {action_id}, Capability: {capability}, Parameters: {str(parameters)}")

        # Send back message *sendActionResult*
        self.send_action_result(action_id, "Everything went fine.")

    def on_config_changed(self):
        """ The configuration of the ActionHandler has changed """
        pass


def wait_for_keypress(websocket: ActionWebSocket):
    input("Press [Enter] to stop.\n")
    websocket.stop()


with ActionWebSocket(api_handler=FixedTokenApiHandler('HIRO_TOKEN')) as ws:
    threading.Thread(daemon=True, target=wait_for_keypress, args=(ws,)).start()
    ws.run_forever()

```

Multithreaded example using a thread executor:

```python
import threading
import concurrent.futures

from hiro_graph_client.actionwebsocket import AbstractActionWebSocketHandler
from hiro_graph_client.clientlib import FixedTokenApiHandler, AbstractTokenApiHandler


class ActionWebSocket(AbstractActionWebSocketHandler):

    def __init__(self, api_handler: AbstractTokenApiHandler):
        """ Initialize properties """
        super().__init__(api_handler)
        self._executor = None

    def start(self) -> None:
        """ Initialize the executor """
        super().start()
        self._executor = concurrent.futures.ThreadPoolExecutor()

    def stop(self, timeout: int = None) -> None:
        """ Shut the executor down """
        if self._executor:
            self._executor.shutdown()
        self._executor = None
        super().stop(timeout)

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


def wait_for_keypress(websocket: ActionWebSocket):
    input("Press [Enter] to stop.\n")
    websocket.stop()


with ActionWebSocket(api_handler=FixedTokenApiHandler('HIRO_TOKEN')) as ws:
    threading.Thread(daemon=True, target=wait_for_keypress, args=(ws,)).start()
    ws.run_forever()

```
