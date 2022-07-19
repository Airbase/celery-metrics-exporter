from time import sleep
from typing import Union

import daiquiri
from celery import Celery
from celery.events.state import Task, Worker

from exporters import Exporter
from utils import is_event_type_task

logger = daiquiri.getLogger(__name__)


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

    def _notify_exporters(self, event: Union[Task, Worker]):
        for exporter in self.exporters:
            exporter.process_event(event)

    def notify(self, event):
        event_type: str = event.get("type")
        if not is_event_type_task(event_type):
            # Since we are only exporting metrics related to celery task
            # worker event can be filtered out
            return

        event_details, event_type = self.state.event(event)
        event, is_create_event = event_details
        logger.debug(
            f"Receiver event: {event.uuid} {event.name}, {event.state} {event.timestamp} with data: {event}"
        )
        self._notify_exporters(event)

    def run(self) -> None:
        with self.celery_app.connection() as connection:
            while True:
                try:
                    receiver = self.celery_app.events.Receiver(
                        connection, handlers={"*": self.notify}
                    )
                    receiver.capture(limit=None, timeout=120)
                except Exception:
                    logger.exception("Exception at CeleryEventReceiver")
                    sleep(10)
