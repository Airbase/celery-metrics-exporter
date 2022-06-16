import logging
from queue import Queue

import click
from kombu.utils.functional import LRUCache

from exporters import DataDogExporter
from receiver import CeleryEventReceiver
from store import InMemoryStore


@click.command()
@click.option("--broker", default="redis://localhost:6379/1", help="celery broker uri")
def run(broker):
    logging.basicConfig(format="[%(levelname)s] %(message)s")

    logging.info("Initialize store")
    store = InMemoryStore(LRUCache(100000), Queue())

    logging.info("Initialize receiver")
    event_receiver = CeleryEventReceiver(broker=broker, store=store)
    event_receiver.start()

    # start all the exporters in different threads
    logging.info("Initialize datadog exporter")
    dd_exporter = DataDogExporter("api_key", store=store)
    dd_exporter.start()

    # data flow: event_receiver -> store -> dd_exporter
    event_receiver.join()
    dd_exporter.join()


if __name__ == "__main__":
    run()