"""Interface to postgres DB."""

import asyncio
import logging
import datetime
import time

import psycopg2

from ae.bb.msgbus import Consumer

L = logging.getLogger()


class DB:
    """Implement interface to postgres DB.

    Simple wrapper around postgres DB. Errors here
    are always fatal. Connection problems block the whole
    machinery, becausae we can. There's a message bus buffering
    data, so we don't have to care.
    """

    def __init__(self, password="", dsn="host=s1 dbnname=aiven user=aiven"):
        """Connect to the DB."""
        self._dsn = dsn
        self._password = password
        self._backoff_time = 2
        self._stmt = \
            """insert into webservers (url,     tstamp,     nw_status,       http_status,     match)
                                values(%(url)s, %(tstamp)s, %(nw_status)s, %(http_status)s, %(match)s)
            """
        self._connect()

    def _connect(self):
        while True:
            try:
                self._conn = psycopg2.connect(dsn=self._dsn, password=self._password)
                L.warning('_connect: self._conn = %s', self._conn)
                return
            except psycopg2.OperationalError:
                L.error('_connect: Cannot connect to %s, sleeping....', self._dsn)
                time.sleep(self._backoff_time)

    def store(self, result):
        """Store one result.

        Retry in connection errors, abort the single insert error.
        We rely on key uniqness to avoid duplicates (url, timestamp),
        so we don't have to do fancy 2 phase commits between postgres
        and Kafka.
        """
        while True:
            _c = self._conn.cursor()
            data = {
                'url': result.url,
                'tstamp': datetime.datetime.fromtimestamp(result.tstamp),
                'nw_status': result.nw_status,
                'http_status': result.http_status,
                'match': result.match}
            L.info('inserting data %s', data)
            try:
                _c.execute(self._stmt, data)
                self._conn.commit()
                return
            except psycopg2.errors.UniqueViolation:
                L.info('Got duplicate  entry %s at %s', data['url'], data['tstamp'])
                self._conn.rollback()
                return
            except psycopg2.errors.AdminShutdown:
                L.exception('DB not reachable')
                # try to reconnect
                self._connect()


def run(pg_dsn, pg_password, kafka_endpoint, topic):
    """Connecto to DB and Kafka and start async processing.

    This runs until the program is terminated. Errors int he kafka endpoint or
    the postgres DSN are not detected before this function call.
    """
    L.debug('run: pg_dsn = %s', pg_dsn)
    db = DB(password='aiven', dsn=pg_dsn)
    c = Consumer(kafka_endpoint, topic, db)
    asyncio.run(c.run())
