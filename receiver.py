import logging
from threading import Thread
from time import sleep

from celery import Celery
from celery.states import READY_STATES

from store import TaskStore
from utils import is_event_type_task

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CeleryEventReceiver(Thread):
    def __init__(self, broker: str, store: TaskStore = None):
        Thread.__init__(self)
        self.daemon = True
        self.broker = broker
        self.store = store
        self.celery_app = Celery(
            broker=self.broker,
        )
        self.state = self.celery_app.events.State()

    def process_event(self, event):
        event_type: str = event.get("type")
        if not is_event_type_task(event_type):
            return

        event_details, event_type = self.state.event(event)
        event, is_create_event = event_details
        logger.debug(
            f"Receiver event: {event.uuid} {event.name}, {event.state} {event.timestamp} with data: {event}"
        )
        self.store.add_event(event.uuid, event.state, event)
        if event.state in READY_STATES:
            logger.info(f"task: {event.uuid} ended with state: {event.state}")
            self.store.add_processable_task(event.uuid)

    def run(self) -> None:
        with self.celery_app.connection() as connection:
            while True:
                try:
                    receiver = self.celery_app.events.Receiver(
                        connection, handlers={"*": self.process_event}
                    )
                    receiver.capture(limit=None, timeout=None)
                except Exception as ex:
                    logger.exception(f"Generic Exception {ex}")
                    sleep(10)
