import logging
from time import sleep
from typing import Union

from celery import Celery
from celery.events.state import Task, Worker

from exporters import Exporter
from utils import is_event_type_task

logger = logging.getLogger(__name__)


class CeleryEventReceiver:
    def __init__(self, broker: str):
        self.broker = broker
        self.celery_app = Celery(
            broker=self.broker,
        )
        self.exporters: list[Exporter] = []
        self.state = self.celery_app.events.State()

    def attach(self, exporter):
        self.exporters.append(exporter)

    def notify(self, event: Union[Task, Worker]):
        for exporter in self.exporters:
            exporter.process_event(event)

    def notify_event(self, event):
        event_type: str = event.get("type")
        if not is_event_type_task(event_type):
            return

        event_details, event_type = self.state.event(event)
        event, is_create_event = event_details
        logger.debug(
            f"Receiver event: {event.uuid} {event.name}, {event.state} {event.timestamp} with data: {event}"
        )
        self.notify(event)

    def run(self) -> None:
        with self.celery_app.connection() as connection:
            while True:
                try:
                    receiver = self.celery_app.events.Receiver(
                        connection, handlers={"*": self.notify_event}
                    )
                    receiver.capture(limit=None, timeout=None)
                except Exception as ex:
                    logger.exception(f"Generic Exception {ex}")
                    sleep(10)
