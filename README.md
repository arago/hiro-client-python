# Python HIRO Clients

This is a client library to access data of the HIRO Graph. It also allows uploads
of huge batches of data in parallel.

## Installation

This project needs at least Python 3.7. 

Install the hiro-client as a python module by using one of the following: 

* Global installation
    ```shell script
    make install
    ```
    or
    ```shell script
    pip3 install src/
    ```
    You need an account with administrative rights to be able to install the tool globally.

* Installation for single user 

    ```shell script
    make install PIPARGS=--user
    ```
    or
    ```shell script
    pip3 install --user src/
    ```
    This will usually install the commandline tool under `${HOME}/.local/bin`.

Take note of warnings while installing the packages, since the installed python executable script might not be part of
the `PATH` environment on your system.

For more details, take a look at the [Makefile](Makefile).



(c) 2020 arago GmbH (https://www.arago.co/)