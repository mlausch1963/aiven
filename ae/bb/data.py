"""Common datastructures.

More or less static structures with conversion methods between serializati0n
format and internal representation.
"""

import json
import logging
import urllib
import re

L = logging.getLogger()


class ServerConfigError(Exception):
    """Application level exception.

    Signals an error in the configuratrion and wraps the original exception.
    """


class ServerConfig:
    """Remote server representation."""

    def __init__(self, url: str, pattern: str = None):
        """Creatws a remote server object to hold url."""
        try:
            res = urllib.parse.urlparse(url)
            if res.scheme not in ['http', 'https']:
                raise ValueError('Invalid scheme')
        except ValueError as ex:
            raise ServerConfigError('Invalid URL') from ex
        self._url = url
        self._re = None
        if pattern:
            try:
                self._re = re.compile(pattern)
            except re.error as exc:
                L.error('Cannot compile regex in entry "%s", regex "%s": %s', url, pattern, exc)
                raise ServerConfigError("Invalid configuration") from exc

    @property
    def url(self) -> str:
        """URL property."""
        return self._url

    @property
    def pattern(self) -> re.Pattern:
        """Regular expression used to match body"""
        return self._re


class Config:
    """Scraper configuration."""

    def __init__(self, f: str = None):
        """Read config from file and parse config."""
        if not f:
            return

        try:
            self._config = json.load(f)
        except json.JSONDecodeError as exc:
            raise ServerConfigError("Invalid JSON content") from exc

        print('self._config = ', self._config)
        try:
            self._servers = [ServerConfig(x['url'], x.get('pattern')) for x in self._config]
        except KeyError as ex:
            L.fatal('Cannot parse config file "g%s": ', ex)
            raise ServerConfigError("Invalid Config file") from ex

        self._interval = 60
        self._topic = None
        self._http_timeout = 50
        self._kafka_producer = 3
        self._kafka_timeout = 7

    @property
    def servers(self) -> str:
        """List of server configs."""
        return self._servers

    @property
    def interval(self) -> int:
        """Return the scrping interval."""
        return self._interval

    @interval.setter
    def interval(self, t: int) -> None:
        """Set the scraping interval."""
        self._interval = t

    @property
    def topic(self) -> str:
        """Return the kafka topic."""
        return self._topic

    @topic.setter
    def topic(self, t: str) -> None:
        """Set the kafka topic."""
        self._topic = t

    @property
    def http_timeout(self) -> int:
        """Return the http timeout."""
        return self._http_timeout

    @http_timeout.setter
    def http_timeout(self, t: int) -> None:
        """Set  the http timeout."""
        self._http_timeout = t

    @property
    def kafka_producer(self) -> int:
        """Retuern the kafka endpoint."""
        return self._kafka_producer

    @kafka_producer.setter
    def kafka_producer(self, p: int) -> None:
        """Return the number of kafka producers."""
        self._Kafka_producer = p

    @property
    def kafka_timeout(self) -> int:
        """Return the kafka timeout."""
        return self._kafka_timout

    @kafka_timeout.setter
    def kafka_timeout(self, t: int) -> None:
        self._kafka_timout = t


class RemoteServerResult:
    """The result of a remote server scrape."""

    def __init__(self,
                 url: str = "",
                 nw_status: str = "",
                 http_status: int = -1,
                 match: bool = True,
                 tstamp: int = 0):
        """Construct a result from  data."""
        self._url = url
        self._nw_status = nw_status
        self._http_status = http_status
        self._match = match
        self._tstamp = tstamp

    @property
    def url(self) -> str:
        """Return url property."""
        return self._url

    @property
    def nw_status(self) -> str:
        """
        Return tuple of network and http status.

        The network status contains
        errors like timeouts, connection resfues, DNS errors and so on.
        """
        if self._nw_status:
            return self._nw_status
        return ''

    @property
    def http_status(self) -> int:
        """Return the http status."""
        return self._http_status

    @property
    def match(self) -> bool:
        """
        Return the result of the regexp match.

        If no regexp match has been executed, return True
        """
        return self._match

    @property
    def tstamp(self) -> int:
        """Return the timestamp as seconds since Epoch."""
        return self._tstamp

    def json(self) -> str:
        """Format and utf-8 encode result."""
        _s = json.dumps({
            'url': self._url,
            'nw_status': str(self._nw_status),
            'http_status': self._http_status,
            'match': self._match,
            'tstamp': self._tstamp
        }, ensure_ascii=False)
        return _s.encode('utf-8')

    @staticmethod
    def from_json(s: str):
        """Convert from JSON representation."""
        _d = json.loads(s)
        if _d['nw_status'] == 'None':
            _d['nw_status'] = ''
        if type(isinstance(_d['match']), bool) \
           and _d['match'].lower() not in ['true', 'false']:
            L.warning('Converting "%s" to True', _d['match'])
            _d['match'] = True
        _o = RemoteServerResult(url=_d['url'],
                                nw_status=_d['nw_status'],
                                http_status=_d['http_status'],
                                match=_d['match'],
                                tstamp=_d['tstamp'])
        return _o
