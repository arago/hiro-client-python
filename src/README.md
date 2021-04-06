# HIRO Graph API Client

This is a client library to access data of the HIRO Graph. It also allows uploads
of huge batches of data in parallel.

__Status__ 

* Technical preview

For more information about HIRO Automation, look at https://www.arago.co/

## HOWTO

To use this library, you will need an account at https://id.arago.co/ and access to an OAuth
Client-Id and Client-Secret to access the HIRO Graph. See also https://developer.hiro.arago.co.

Most of the documentation is done in the sourcecode.

Example to use the straightforward graph api client without any batch processing:

```python
from hiro_graph_client import HiroGraph

hiro_client = HiroGraph(
    username='',
    password='',
    client_id='',
    client_secret='',
    graph_endpoint='https://[server]:8443/api/graph/7.4',  # see https://developer.hiro.arago.co/7.0/api/
    auth_endpoint='https://[server]:8443/api/auth/6' # see https://developer.hiro.arago.co/7.0/api/
)
 
# The commands of the Graph API are methods of the class HIROGraph.
# The next line executes a vertex query for instance. 
query_result = hiro_client.query('ogit\\/_type:"ogit/MARS/Machine"')
 
print(query_result)
```

Example to use the batch client to process a batch of requests:

```python
from hiro_graph_client import HiroGraphBatch

hiro_batch_client = HiroGraphBatch(
    username='',
    password='',
    client_id='',
    client_secret='',
    graph_endpoint='https://[server]:8443/api/graph/7.4',  # see https://developer.hiro.arago.co/7.0/api/
    auth_endpoint='https://[server]:8443/api/auth/6' # see https://developer.hiro.arago.co/7.0/api/
)

# See code documentation about the possible commands and their attributes.
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

Example to use the batch client to process a batch of requests with callbacks for each result:

```python
from hiro_graph_client import HiroGraphBatch, HiroResultCallback

class RunBatch(HiroResultCallback):
    hiro_batch_client: HiroGraphBatch

    def __init__(self,
                 username: str,
                 password: str,
                 client_id: str,
                 client_secret: str,
                 graph_endpoint: str,
                 auth_endpoint: str):
        self.hiro_batch_client = HiroGraphBatch(
            callback=self,
            graph_endpoint=graph_endpoint,
            auth_endpoint=auth_endpoint,
            username=username,
            password=password,
            client_id=client_id,
            client_secret=client_secret
        )

    # This (abstract) method gets called for each command when results are available
    def result(self, data: Any, code: int) -> None:
        print('Data: ' + str(data))
        print('Code: ' + str(code))

    def run(self, commands: Iterator[dict]):
        self.hiro_batch_client.multi_command(commands)


batch_runner = RunBatch(
    username='',
    password='',
    client_id='',
    client_secret='',
    graph_endpoint='https://[server]:8443/api/graph/7.4',  # see https://developer.hiro.arago.co/7.0/api/
    auth_endpoint='https://[server]:8443/api/auth/6' # see https://developer.hiro.arago.co/7.0/api/
)

# See code documentation about the possible commands and their attributes.
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

batch_runner.run(commands)
```

(c) 2020 arago GmbH