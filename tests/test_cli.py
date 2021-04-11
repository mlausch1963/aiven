#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
.. currentmodule:: test_cli
.. moduleauthor:: Michael Lausch <mick.lausch@gmail.com>

This is the test module for the project's command-line interface (CLI)
module.
"""
# fmt: off
import ae.cli as cli
from ae import __version__
import psycopg2
import kafka

from unittest.mock import patch, mock_open
import pytest

import pytest_mock as pm
# fmt: on
from click.testing import CliRunner, Result


# To learn more about testing Click applications, visit the link below.
# http://click.pocoo.org/5/testing/


def test_version_displays_library_version():
    """
    Arrange/Act: Run the `version` subcommand.
    Assert: The output matches the library version.
    """
    runner: CliRunner = CliRunner()
    result: Result = runner.invoke(cli.cli, ["version"])
    assert (
        __version__ in result.output.strip()
    ), "Version number should match library version."


def test_verbose_output():
    """
    Arrange/Act: Run the `version` subcommand with the '-v' flag.
    Assert: The output indicates verbose logging is enabled.
    """
    runner: CliRunner = CliRunner()
    result: Result = runner.invoke(cli.cli, ["-v", "version"])
    assert (
        "Verbose" in result.output.strip()
    ), "Verbose logging should be indicated in output."


def test_scraper_no_options():
    """Test with no params at all."""
    runner: CliRunner = CliRunner()
    # scrape
    result: Result = runner.invoke(cli.cli, ["scrape"])
    assert (
        "Error: Missing option" in result.output.strip()
    ), "No params at all."


def test_scraper_missing_topic_option():
    """Test with only --config params."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        open("xx", "w").close()
        result = runner.invoke(cli.cli, ["scrape", "--config", "xx"])

        assert (
            "--topic" in result.output.strip()
        ), "Missing --topic option."


def test_scraper_missing_config_option():
    """Test with only --topic params."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        open("xx","w").close()
        result = runner.invoke(cli.cli, ["scrape", "--topic", "xx"])

        assert (
            "--config" in result.output.strip()
        ), "Missing --config option."


def test_store_no_options():
    """Test store with no options."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["store"])
    assert (
        "--postgres_dsn" in result.output.strip()
    ), "'store' with No options."


def test_store_missing_with_dsn_no_topic():
    """Test store with no options."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["store",
                                     "--postgres_dsn", "host='s1' user='not_existing' dbname='aiven'"])
    assert (
        "--postgres_password" in result.output.strip()
    ), "'store' with dsn."


def test_store_missing_topic():
    """Test store with no options."""
    runner = CliRunner()
    result = runner.invoke(cli.cli, ["store",
                                     "--postgres_dsn", "host='s1' user='not_existing'  dbname='aiven'",
                                     "--postgres_password", "aa"])
    assert (
        "--topic" in result.output.strip()
    ), "'store' with missing topic."


def test_store_valid_options(mocker):
    """Test store with valid options."""
    runner = CliRunner()
    mocker.patch('psycopg2.connect', return_value=None)
    x = None
    result = runner.invoke(cli.cli, ["store",
                                     "--postgres_dsn", "host='s1' user='no_existing' dbname='aiven'",
                                     "--postgres_password", "aa",
                                     "--topic", "test"
                                     ])
    assert (isinstance(result.exception, SystemExit))
    assert (result.exit_code == 1), "Error exit"
