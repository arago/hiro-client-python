# Python HIRO Clients

This is a client library to access data of the HIRO Graph. It also allows uploads
of huge batches of data in parallel.

## Installation

This project needs at least Python 3.7. 

Install the hiro-client as a python package by using one of the following: 

* Global installation
    ```shell script
    make install
    ```
    or
    ```shell script
    pip3 install src/
    ```
    You need an account with administrative rights to be able to install the package globally.

* Installation for single user 

    ```shell script
    make install PIPARGS=--user
    ```
    or
    ```shell script
    pip3 install --user src/
    ```

For more details, take a look at the [Makefile](Makefile) and the [README.md in src](src).



(c) 2020 arago GmbH (https://www.arago.co/)
