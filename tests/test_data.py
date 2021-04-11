#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import time

import pytest
import pyfakefs

import ae


def test_data_emppty_config_file(fs):
    """Test for exmpty config file."""
    fs.create_file("xx")
    with pytest.raises(ae.bb.data.ServerConfigError) as e:
        sc = ae.bb.data.Config(open("xx", "r"))

def test_data_empty_server_array(fs):
    """Test for exmpty config file."""

    fs.create_file("xx", contents="[]")
    sc = ae.bb.data.Config(open("xx", "r"))
    assert (sc.servers == []), "Empty server list."


def test_data_one_server_entry(fs):
    """Test for one entry config file."""

    fs.create_file("xx", contents='[{"url": "http://www.example.com"}]')
    sc = ae.bb.data.Config(open("xx", "r"))
    assert (len(sc.servers) == 1), "One element server list."
    assert (isinstance(sc.servers[0], ae.bb.data.ServerConfig)), "ServerConfigType."
    assert(sc.servers[0].url == 'http://www.example.com'), "server url"

def test_data_two_server_entry(fs):
    """Test for one entry config file."""

    fs.create_file("xx", contents="""
[
  {"url": "http://www.example.com"},
  {
     "url": "https://www2.example.com",
     "pattern": ".*"
  }
]
    """)
    sc = ae.bb.data.Config(open("xx", "r"))
    assert (len(sc.servers) == 2), "One element server list."
    assert (isinstance(sc.servers[0], ae.bb.data.ServerConfig)), "ServerConfigType."
    assert(sc.servers[0].url == 'http://www.example.com'), "server0 url"
    assert(sc.servers[1].url == 'https://www2.example.com'), "server1 url"
    assert(sc.servers[1].pattern == re.compile('.*')), "server pattern"


def test_data_missing_url(fs):
    """Test for one entry config file."""

    fs.create_file("xx", contents="""
[
  {
     "pattern": ".*"
  }
]
    """)
    with pytest.raises(ae.bb.data.ServerConfigError) as e:
        sc = ae.bb.data.Config(open("xx", "r"))


def test_data_inbvalid_URL(fs):
    """Test for one entry config file."""

    fs.create_file("xx", contents="""
[
  {
    "url": "example.com:9092"
  }
]
    """)
    with pytest.raises(ae.bb.data.ServerConfigError) as e:
        sc = ae.bb.data.Config(open("xx", "r"))


def test_data__srv_result_to_json():
    now = time.time()
    r = ae.bb.data.RemoteServerResult(
        url='http://www.example.com',
        nw_status='nw_status',
        http_status=200,
        match=False,
        tstamp=now)
    assert (r.url == 'http://www.example.com'), 'result.url'
    assert (r.nw_status == 'nw_status'), 'result.nw_status'
    assert (r.http_status == 200), 'result.http_status'
    assert (r.match == False), 'result.match'
    assert (r.tstamp == now), 'result.tstamp'

def test_data_srv_to_json():
    now = time.time()
    d = {
        'url': 'http://www.example.com',
        'nw_status': 'nw_status',
        'http_status': 200,
        'match': False,
        'tstamp': now
    }
    r = ae.bb.data.RemoteServerResult(
        url=d['url'],
        nw_status=d['nw_status'],
        http_status=d[str('http_status')],
        match=d['match'],
        tstamp=d['tstamp'])
    expected = json.dumps(d).encode('utf-8')
    j = r.json()
    assert (j == expected), 'to json serialization'
