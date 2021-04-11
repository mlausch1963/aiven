"""Async scraper fo websites."""

import re
import logging
import time
import asyncio
import aiohttp
import sys

from typing import TextIO

from ae.bb.msgbus import Producer
from ae.bb.data import RemoteServerResult, ServerConfig, Config

L = logging.getLogger('scraper')


class Scraper:
    """
    Scrapes the webservers.

    Does regexp matching on the bodies and enqueues.
    results into the Kafka client queue.
    """

    def __init__(self, config: Config, q: asyncio.Queue):
        """Init scraper  with list of servers to scrape."""
        self._queue = q
        self._http_timeout = config.http_timeout
        self._servers = config.servers
        self._producers = []

    async def _fetch(self, client: aiohttp.ClientSession, server: ServerConfig) -> None:
        """Async fetch of one server.

        Polls one server and puts result in the queue.
        """
        while True:
            start_time = time.clock_gettime(time.CLOCK_MONOTONIC)
            try:
                L.info('_fetch: fetching %s with timeout %d secs', server.url,
                       self._http_timeout)

                resp = await client.get(server.url, timeout=self._http_timeout)
                # enqueue it to kafka
                L.debug('fetch: url = "%s", resp.status = "%s"', server.url,
                        resp.status)
                bdy = await resp.text()
                match = False
                if server.pattern:
                    match = re.search(server.pattern, bdy) is not None
                    L.debug('Body pattern match result: %s,  body = %s, pattern = %s', match, bdy[:80], server.pattern)
                result = RemoteServerResult(server.url,
                                            None,
                                            resp.status,
                                            match,
                                            tstamp=time.time())
            except aiohttp.client_exceptions.ClientError as exc:
                L.exception('fetch: client exception: url = "%s", exception = "%s"',
                            server.url, exc)
                result = RemoteServerResult(server.url,
                                            exc,
                                            None,
                                            False,
                                            tstamp=time.time())
            except asyncio.TimeoutError:
                L.warning('fetch timeout: url = "%s"', server.url)
                result = RemoteServerResult(server.url,
                                            "Timeout",
                                            None,
                                            False,
                                            tstamp=time.time())
            except Exception as exc:
                L.error('_fetch: Uncaught exception: url = "%s, exc = %s', server.url, exc)
                result = RemoteServerResult(server.url,
                                            "Uncaught Exception: {0}".format(exc),
                                            None,
                                            False,
                                            tstamp=time.time())

            L.debug("_fetch: enqueueing to kafka: %s", result.json()[:128])
            await self._queue.put(result)
            used = time.clock_gettime(time.CLOCK_MONOTONIC) - start_time
            timeout = self._http_timeout - used
            L.debug("_fetch: sleeping %d for url %s", timeout, server.url)
            await asyncio.sleep(timeout)
            L.debug('_fetchj: Done sleep, new iteration starts')

    async def producers(self, client):
        """Create a list with one task per scrape target and return the list."""
        self._producers = [asyncio.create_task(self._fetch(client, server))
                           for server in self._servers]
        return self._producers

    async def cancel(self, *args):
        """Cancel running tasks."""
        L.warning('cancel: args = %s', args)
        for p in self._producers:
            p.cancel()
        await self._queue.join()


async def run(c: Config) -> None:
    """Init the async tasks and start them.

    Creates one scrape task per URL, 'producer' number of kafka producers and
    connects then via an async queue. The fetchers push ServerResults into the
    queue, and the kafka producers send the result to the Kafka broker.

    It is assumed, that the broker is available. The queue is only here to
    decouple the scraper from the kafka producer.

    FIXME: the queue should be of limited capacity, at least as big as the
    number of scrape targets, at most N times the  number of scrape targets,
    which will buffer N measurements.
    """
    q = asyncio.Queue()
    kp = Producer(c.kafka_endpoint, c.kafka_producer, c.topic, q)
    await kp.init()

    s = Scraper(c, q)
    async with aiohttp.ClientSession() as client:
        producers = await s.producers(client)
        _ = await kp.kafka_producers()
        while True:
            try:
                await asyncio.gather(*producers)
                await q.join()
            except asyncio.exceptions.CancelledError:
                L.warning('main run: cancelled')
                await q.join()
                return
    L.debug('main run: done')


def _check_timeouts(interval, http_timeout, kafka_timeout):
    """Checkf for timeout validity.

    kafka_timeout + http_timeout < interval + fudge (2 secs for now)
    otherwise that's a fatal error.
    """
    _fudge = 2
    if (kafka_timeout + http_timeout) < (interval + _fudge):
        return True
    else:
        L.error("kafka_timeout(%d) + http_timeout(%d) < interval(%d) + fudge(2) violated",
                kafka_timeout, http_timeout, interval)


def start(config_file: TextIO,
          topic: str,
          interval: int,
          http_timeout: int,
          kafka_endpoint: str,
          kafka_producer: int,
          kafka_timeout: int):
    """Run the main loop."""
    if not _check_timeouts(interval, http_timeout, kafka_timeout):
        L.fatal('Aborting.')
        sys.exit(1)

    c = Config(config_file)
    c.topic = topic
    c.interval = interval
    c.http_timeout = http_timeout
    c.kafka_endpoint = kafka_endpoint
    c.kafka_producer = kafka_producer
    c.kafka_timeout = kafka_timeout
    asyncio.run(run(c))
