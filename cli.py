import logging
import os
import sys

import click
import daiquiri
from pythonjsonlogger.jsonlogger import JsonFormatter

from exporters import DataDogExporter
from receiver import CeleryEventReceiver
from store import InMemoryStore


def setup_logging():
    prod_log_format = (
        "%(asctime)s [%(process)d] %(levelname)-8.8s %(name)s: %(message)s"
    )
    is_production_env = os.environ.get("PROD", "False").lower() == "true"
    output_formatter = (
        JsonFormatter(prod_log_format)
        if is_production_env
        else daiquiri.formatter.ColorFormatter()
    )
    daiquiri.setup(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        outputs=[
            daiquiri.output.Stream(sys.stdout, formatter=output_formatter),
        ],
    )


@click.command()
@click.option("--broker", default="redis://localhost:6379/1", help="celery broker uri")
def run(broker):
    setup_logging()

    # start all the exporters in different threads
    logging.info("Initialize datadog exporter")
    dd_exporter = DataDogExporter(store=InMemoryStore(max_size=100000))
    dd_exporter.start()

    logging.info("Initialize receiver")
    event_receiver = CeleryEventReceiver(broker=broker)
    event_receiver.attach(dd_exporter)
    event_receiver.run()


if __name__ == "__main__":
    run()
