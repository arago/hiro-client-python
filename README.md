# HIRO Client Python

This is a client library to access data of the HIRO Graph.

To process large batches of data, take a look at [hiro-batch-client](https://github.com/arago/hiro-client-python/tree/separate_hiro_batch_client).

## Installation

This project needs at least Python 3.7. 

If you need the library without any sources, you can install the compiled package directly from [PyPI](https://pypi.org/project/hiro-graph-client) via:

```shell script
pip3 install hiro-graph-client
```

To install the hiro-client from source as a python package, use one of the following: 

* Global installation
    ```shell script
    make install
    ```
    or
    ```shell script
    pip3 install --use-feature=in-tree-build src/
    ```
    You need an account with administrative rights to be able to install the package globally.

* Installation for single user 

    ```shell script
    make install PIPARGS=--user
    ```
    or
    ```shell script
    pip3 install --use-feature=in-tree-build --user src/
    ```

For more details, take a look at the [Makefile](Makefile)

## Documentation

Look at [README.md in src](src).



(c) 2022 arago GmbH (https://www.arago.co/)
