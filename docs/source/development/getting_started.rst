.. _getting_started_dev:

.. toctree::
    :glob:

***************
Getting Started
***************

This section provides instructions for setting up your development environment.  If you follow the
steps from top to bottom you should be ready to roll by the end.


Get the Source
==============

The source code for the `AivenExercise` project lives at
`github <https://github.com/mlausch1963/AivenExercise>`_.
You can use `git clone` to get it.

.. code-block:: bash

   git clone https://github.com/patdaburu/bnrml

Create the Virtual Environment
==============================

You can create a virtual environment and install the project's dependencies using :ref:`make <make>`.

.. code-block:: bash

    make venv
    make install
    source venv/bin/activate

Try It Out
==========

One way to test out the environment is to run the tests.  You can do this with the `make test`
target.

.. code-block:: bash

    make test

If the tests run and pass, you're ready to roll.

Getting Answers
===============

Once the environment is set up, you can perform a quick build of this project
documentation using the `make answers` target.

.. code-block:: bash

    make answers


TODO
============

Enhance the scrape configuration by a method (GET/POST/...), optional headers
fields which may be useful for authn/z, like bearer token.

Unit tests for the async machinery are missing. I don't think they are worth the
effort. An automated setup with some URL, showing different errors and URL
pointint to server which don't exist, as well as a standard kafka message bus,
and running kafkacat checking the writes to Kafka make more sense.

For the database side a default postgresql installation and using the packaged
utils/create_table.sql as the sink, and a kafkacat sending prepared JSON
payloads to the message bus, as well as a simple script compoaring the stored
data from the database with the prepared JSON files will be good enough.
