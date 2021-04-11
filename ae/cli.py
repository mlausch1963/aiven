#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is the entry point for the command-line interface (CLI) application.

It can be used as a handy facility for running the task from a command line.

.. note::

    To learn more about Click visit the
    `project website <http://click.pocoo.org/5/>`_.  There is also a very
    helpful `tutorial video <https://www.youtube.com/watch?v=kNke39OZ2k0>`_.

    To learn more about running Luigi, visit the Luigi project's
    `Read-The-Docs <http://luigi.readthedocs.io/en/stable/>`_ page.

.. currentmodule:: ae.cli
.. moduleauthor:: Michael Lausch <mick.lausch@gmail.com>
"""
import logging
import coloredlogs
import click
from ae.bb import scraper
from ae.bb import storage

from typing import TextIO

from .__init__ import __version__

L = logging.getLogger()

LOGGING_LEVELS = {
    0: logging.NOTSET,
    1: logging.ERROR,
    2: logging.WARN,
    3: logging.INFO,
    4: logging.DEBUG,
}  #: a mapping of `verbose` option counts to logging levels


class Info:
    """An information object to pass data between CLI functions."""

    def __init__(self):  # Note: This object must have an empty constructor.
        """Create a new instance."""
        self.verbose: int = 0
        self.config_file: str = ""


# pass_info is a decorator for functions that pass 'Info' objects.
#: pylint: disable=invalid-name
pass_info = click.make_pass_decorator(Info, ensure=True)


# Change the options to below to suit the actual options for your task (or
# tasks).
@click.group(name='ae')
@click.option("--verbose", "-v", count=True, help="Enable verbose output.")
@pass_info
def cli(info: Info, verbose: int):
    """Run ae."""
    # Use the verbosity count to determine the logging level...
    if verbose > 0:
        logging.basicConfig(
            level=LOGGING_LEVELS[verbose]
            if verbose in LOGGING_LEVELS
            else logging.DEBUG
        )
        click.echo(
            click.style(
                f"Verbose logging is enabled. "
                f"(LEVEL={logging.getLogger().getEffectiveLevel()})",
                fg="yellow",
            )
        )
        coloredlogs.install(LOGGING_LEVELS[verbose])
    info.verbose = verbose


@cli.command()
@click.option("--config", "-c", type=click.File("r"), required=True)
@click.option("--topic", "-t", type=str, required=True)
@click.option("--interval", "-i", type=int, default=60)
@click.option("--http_timeout", type=int, default=50)
@click.option("--kafka_endpoint", type=str, default="localhost:9092")
@click.option("--kafka_producer", type=int, default=3)
@click.option("--kafka_timeout", type=int, default=7)
@pass_info
def scrape(_: Info,
           config: TextIO,
           topic: str,
           interval: int,
           http_timeout: int,
           kafka_endpoint: str,
           kafka_producer: int,
           kafka_timeout: int) -> None:
    """Start the srcaper component."""
    scraper.start(config,
                  topic,
                  interval,
                  http_timeout,
                  kafka_endpoint,
                  kafka_producer,
                  kafka_timeout)


@cli.command()
@click.option("--postgres_dsn", type=str, required=True)
@click.option("--postgres_password", type=str, required=True)
@click.option("--kafka_endpoint", type=str, default='localhost:9091')
@click.option("--topic", type=str, required=True)
@pass_info
def store(_: Info,
          kafka_endpoint,
          topic,
          postgres_dsn: str,
          postgres_password: str) -> None:
    """Start the store componment."""
    L.debug("postgres_dsn = %s", postgres_dsn)
    storage.run(postgres_dsn, postgres_password, kafka_endpoint, topic)


@cli.command()
def version():
    """Get the program version."""
    click.echo(click.style(f"{__version__}", bold=True))


if __name__ == '__main__':
    cli()
