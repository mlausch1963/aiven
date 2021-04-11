.. _development:

Design
===========

The system is more complicated as it needs to be and the usage of a message bus
between the scraper and the store serves no real purpose. The frequence of

The system uses Python's asyncio framework in the scraper part. It does not use
it in the store part.

The required throughput of the complete system is constant. There are no spikes
and troughs, because scrpaing, and therefore data generation happens in a fixed
pace. The asyncio framework in the scraper part was chosen, because it is
expected that most of thje webservers are up and answer with sub-second
latency. That would make the system process the most of the defined endpoints in
the first second of the interval. Therefore high performance in this area is
crucial.

After the messagebus, in the `store` component, peak performance is not so
important. By
using groups (the groupid is currently hardcoded), we can run multiple copies of
the  the `store` component in parallel, pootentially in different servers (which
is good for reliability) until the performance envelop of the Kafka bus or the
postgres database is exceeded.

Storing timeseries data in a plain postgres database is a waste of
space. Specialized compression methods for timeseries data are able to shrink
down one measurement point to 1 to 1.5 bytes
(https://blog.acolyer.org/2016/05/03/gorilla-a-fast-scalable-in-memory-time-series-database/).
Similar algorithms, which disk persistence, are available.

If storage in a relational database is a hard requirement, something like
TimescapeDB should be used, which provides transparent sharding support and is
based on PostgreSQL.

Transactional Behaviour
-------------------------

We want every measurement to be in the database exactly once, therefore a
transaction spawns the whole sequence from scraping to processing in the Kafka
bus, to storing in the database. This is a multiple stages transcation. To avoid
the implementation of 2 Phase Commits all over the place, especially in the
``store`` component, we establish the following properties:

- we don't care about the time difference in measurements. They aren't accurate
  anyway and jitter and can elimineted when reading the data from the database.
- we don't want one scrape sequence with the same timestamp stored int he
  database.

With these 2 requirement we can build a system with multiple ``scrapers``, running
in parallel with the same configuration, guarding against failure of one
service. We can also run multiple ``stores`` to the same effect. Idempotency is
achieved only at the database level with a unique index spawning the ``url``
and the ``timestamp``.


Reliability
-----------

The reliability of serial systems is

.. math::
   R = \prod P_n

where P\ :sub:`n`\ is the reliability of a system.

By setting the reliability to 0.995 for all the systems in the chain, we get
a reliability of

.. code:: python

   0.995 * 0.995 * 0.995 * 0.995

which is 0.8145, which is an uptime of 81%. Not so great.  And 99.5% is a
downtime of 1.8 days per year, or 3.6 hours per month.

Reliability cvan ba improved by removing all the steps and simply scrape and
store the data  in one process, using a queue between the scraper and the
storage backend to flatten out peks (see Design).

The queue must be able to store exactly one entry per server. Each entry
consists of:


+--------------+-----+
|Name          |Size |
+--------------+-----+
| url          |256  |
+--------------+-----+
| http_status  |4    |
+--------------+-----+
|network_status|200  |
+--------------+-----+
|match         | 1   |
+--------------+-----+
|tstamp        | 4   |
+--------------+-----+

Which is sum 465 bytes per entry. Add some overhead and it's 500 bytes per
entry. Allocating 100M of memory, that is enough for 20_000 servers per
instance. And it's easy to run as many instances in parrallel and therefore do
simpel sharding. You can also run more than one instance targetting the same set
of servers in parallel, improving reliability


.. toctree::
   :maxdepth: 1
   :caption: Contents:

   Design
   Reliability


Indices and tables
======================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
