import logging
import os
import sys

import click
import daiquiri
from pythonjsonlogger.jsonlogger import JsonFormatter

from exporters import DataDogExporter, PostgresExporter
from receiver import CeleryEventReceiver
from settings import POSTGRES_URI
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
@click.option("--exporters", default="datadog,postgres", help="list of exporters")
def run(broker, exporters):
    setup_logging()

    exporters_config = exporters.split(",")
    exporters_list = []
    # start all the exporters in different threads
    if "datadog" in exporters_config:
        logging.info("Initialize datadog exporter")
        dd_exporter = DataDogExporter(store=InMemoryStore(max_size=100000))
        dd_exporter.start()
        exporters_list.append(dd_exporter)

    if "postgres" in exporters_config:
        logging.info("Initialize postgres exporter")
        postgres_exporter = PostgresExporter(dburi=POSTGRES_URI)
        postgres_exporter.start()
        exporters_list.append(postgres_exporter)

    logging.info("Initialize receiver")
    event_receiver = CeleryEventReceiver(broker=broker)
    for exporter in exporters_list:
        event_receiver.attach(exporter)
    event_receiver.run()


if __name__ == "__main__":
    run()
