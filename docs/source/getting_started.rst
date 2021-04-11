.. _getting_started:

.. toctree::
    :glob:

***************
Getting Started
***************

The whole system consists of two daemons, one probing or scraping the webservers
and writing the results as JSON encoded data into a Kafka bus, the second one
reading from the Kafka bus and storing the data into a postgres table.


Installing the Components
============================

You can use setup.py to install `ae`.

.. code-block:: sh

    python3 setup.py install

All the usual setup.py install methods are supporeted. It is recommneded to
install into a python environment.

Database Setup
==================

the ``utils/create_table.sql`` directory contains a PostgresQL script which
creates the database table, as well as necessary indices necessary to implement
idempotency.

+-----------+----------+--------------+
|Column     |Type      |Remarks       |
|Name       |          |              |
+-----------+----------+--------------+
| url       |varchar   |the URL of    |
|           |          |the scrape    |
|           |          |endpint       |
|           |          |              |
|           |          |              |
+-----------+----------+--------------+
|tstamnp    |integer   |seconds       |
|           |          |froim the     |
|           |          |epooch where  |
|           |          |the http      |
|           |          |request was   |
|           |          |sent to the   |
|           |          |target. No    |
|           |          |timezone,     |
|           |          |it's          |
|           |          |basically     |
|           |          |UTC.          |
+-----------+----------+--------------+
|match      |boolean   |set to        |
|           |          |``False`` if  |
|           |          |there was a   |
|           |          |pattern in the|
|           |          |scrape        |
|           |          |cxondifuration|
|           |          |and it didn't |
|           |          |match,        |
|           |          |``True``      |
|           |          |otherwise     |
+-----------+----------+--------------+
|http_status|the HTTP  |              |
|           |status    |              |
|           |code as   |              |
|           |integer   |              |
+-----------+----------+--------------+
|nw_status  |varchar   |any network   |
|           |          |level error,  |
|           |          |DNS errors,   |
|           |          |TLS errors as |
|           |          |free text, as |
|           |          |delivbered by |
|           |          |the underlying|
|           |          |libraries;    |
|           |          |Processing may|
|           |          |be done when  |
|           |          |reading with  |
|           |          |stored        |
|           |          |prodcedures.  |
|           |          |              |
+-----------+----------+--------------+



Running the Scraper
===================

The scraper  is started

.. code-block:: sh

    ae scrape --config <config file>
              --topic <Kafka topic>
              [ --interval <seconds> ]
              [ --http_timeout <seconds> ]
              [ --kafka_endpoint <host:port> ]
              [ --kafka_producer <integer> ]


This will read a list of JSON formatted scrape targets from :code:`config
file`.
A
sample of the json file can be found int he ``config.sample`` file in the source
root directory. It consists of an array of entries, each entry has a mandatory
URL, which is the scrape target, and an optional ``pattern`` element, which is a
regexp. The ``pattern`` regexp is searched int he body of the webserver
response. If the regexp can be found, the ``match`` column in the database is set
to ``true``.

The servers in the config file are contacted once every ``interval`` seconds
witth an overall timeout (conenction, transfer) of ``http_timeout``
seconds.

After searching the regular expression from the server config in body the http
status, network status, like no DNS entry, connection refused, or invalid TLS
certificate are written to the Kafka bus.

Writing to the Kafka bus is done by ``kafka_producer`` instances of an async
Kafka producer and written to the topic ``topid``. The producers also have a
time out, which is ``kafka_timeout`` seconds. The Kafka discovery endpoint is
giben as ``kafka_endpoint``.

The timeouts must satisfy the condition:

.. code-block:: python

    (http_timeout + kafka_timeout) < (interval - fudge)

where :code:`fudge` is 2 seconds. Otherwise the program logs and error and
stops.

Running the Storage
================

The storage part is started

.. code-block:: sh

    ae store --postgres_dsn <dsn>
             --postgres_password <password>
             --kafka_endpoint <host:port>
             --topic <topic>

This will read messages from the kafka endpoint ``kafka_endpoint``, with the
topic ``topic``, decode the JSON payload and
stoee them into the postgres database ``dsn`` using ``password`` for
authentication. The password can and *should* be passed to the program in an
environment variable `POSTGRES_PASSOWRD`, to hide it from :code:`ps  -edalf`
queries.

A typical postgres DSN looks like this
``host=dbserver.example.com dbname=aiven  user=aiven``. Details can be found at
https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING

Common Flags
================

The common flags to the ``ae`` system are

.. code-block:: sh

    ae [-v] [-v -v -v] [--help ]

The ``-v`` option increases verbosity of the log output. Passing ``--help`` or
no parameters at all, prints general usage information.
