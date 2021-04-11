"""Producer and consumer implementation for Kafka msgbus."""

import asyncio
import kafka
import logging

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from ae.bb.data import RemoteServerResult

L = logging.getLogger('msgbus')


class Producer:
    """Sends results to Kafka.

    It uses the asyncio Kafka library with multiple tasks, but only
    one Kafka producer.
    TODO: Maybe more  producers get better performance,
    if they connect to different nodes in a Kafka cluster. This needs
    some bench-marking and error simulations.
    """

    def __init__(self, endpoint: str, pcount: int, topic: str,
                 q: asyncio.Queue):
        """Init producer with endpoint and topic."""
        self._topic = topic
        self._kafka = None
        self._producers = []
        self.numof_producers = pcount
        self._endpoint = endpoint
        self._queue = q
        self._connect_timeout = 10
        self._retry_backoff = 2 * 1000

    async def init(self):
        """Block on initializing the async Kafka producer."""
        # FIXME: As with he consumer, a loop with exp backoff makes
        #        sense here. Would make orchestration easier.
        self._kafka = AIOKafkaProducer(bootstrap_servers=self._endpoint,
                                       retry_backoff_ms=self._retry_backoff)
        return await asyncio.wait_for(self._kafka.start(), self._connect_timeout)

    async def _send(self, idx: int) -> None:
        """Dequeue item and send to Kafka"""
        while True:
            try:
                msg = await self._queue.get()
                L.info('_send[%d]: dequeued "%s"', idx, msg)
                await self._kafka.send_and_wait(self._topic, msg.json())
                self._queue.task_done()
            except Exception:
                L.exception('_send[%d] exception', idx)

    async def kafka_producers(self):
        """Create a list of kafka producer tasks."""
        producers = [asyncio.create_task(self._send(i))
                     for i in range(self.numof_producers)]
        self._producers = [await p for p in producers]
        return self._producers

    async def cancel(self, *_):
        """Close connection to Kafka."""
        L.error("shutdown: not yet implemented.")
        for p in self._producers:
            p.cancel()

    async def _close(self):
        await self._kafka.stop()


class Consumer:
    """Fetch message from bus and send to storage for persisting."""

    def __init__(self, endpoint, topic, db):
        """Initialize config data for the consumer.

        The real connection to the kafka message bus and the database is
        creatred when  the aync machinery is started int he `run`function.
        Therefore errors are delayed until that point.
        """
        self._topic = topic
        self._endpoint = endpoint
        self._tasks = []
        self._db = db
        self._retry_backoff = 2 * 1000  # 2 seconds backoff for retries
        self._consumer = None

    async def _init_me(self):
        L.debug('_init_me: called')

        self._consumer = AIOKafkaConsumer(self._topic,
                                          group_id='g1',
                                          auto_offset_reset='earliest',
                                          enable_auto_commit=True,
                                          retry_backoff_ms=self._retry_backoff,
                                          bootstrap_servers=self._endpoint)
        # FIXME: We should loop  here with exp backoff and try to connect to
        #         the msgbus. That would make it easiert to start components
        #         out of order and lessen the complexity of orchestration.
        try:
            return await self._consumer.start()
        except kafka.errors.KafkaConnectionError:
            L.exception('Consumer start failed')
            L.fatal('Aborting')
            raise SystemExit(1)

    async def _process(self, msg):
        _v = msg.value
        L.info('msg.value = %s', _v)
        try:
            result = RemoteServerResult.from_json(_v)
        except KeyError:
            L.warning("_process: malformatted JSON message, ignoring")
            return
        self._db.store(result)

    async def run(self):
        """Run the consumer loop.

        Wait for consumer to complete initialization, then
        fetch messages, process them and commit them batck to the message bus.
        """
        L.debug('run: Waiting for messages')

        await self._init_me()
        L.debug('run: self._consumer = %s', self._consumer)

        while True:
            result = await self._consumer.getmany(timeout_ms=10 * 1000)
            L.info("run: result = %s", result)
            for tp, messages in result.items():
                L.debug("tp = %s, messages = %s", tp, messages)
                if messages:
                    L.debug("run: messages processing")
                    for msg in messages:
                        await self._process(msg)
                    L.info("run: commiting offset %d", messages[-1].offset + 1)
                    await self._consumer.commit({tp: messages[-1].offset + 1})
                    L.info('run: commited')

    def shutdown(self, loop):
        """Start synchronously the async postgres consumer."""
        loop.run_until_complete(self._close())
        self._consumer = None

    async def _close(self):
        await self._consumer.stop()
