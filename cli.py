import logging
import os

import click

from exporters import DataDogExporter
from receiver import CeleryEventReceiver
from store import InMemoryStore


@click.command()
@click.option("--broker", default="redis://localhost:6379/1", help="celery broker uri")
def run(broker):
    logging.basicConfig(
        format="[%(levelname)s] %(message)s", level=os.environ.get("LOG_LEVEL")
    )

    logging.info("Initialize store")
    store = InMemoryStore(max_size=100000)

    logging.info("Initialize receiver")
    event_receiver = CeleryEventReceiver(broker=broker)
    event_receiver.start()

    # start all the exporters in different threads
    logging.info("Initialize datadog exporter")
    dd_exporter = DataDogExporter(store=store)
    event_receiver.attach(dd_exporter)
    dd_exporter.start()

    event_receiver.join()
    dd_exporter.join()


if __name__ == "__main__":
    run()
