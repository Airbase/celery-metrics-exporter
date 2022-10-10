import json
from datetime import datetime
from queue import Queue
from threading import Thread
from time import sleep
from typing import Union

import daiquiri
from celery.events.state import Task as TaskEvent
from celery.events.state import Worker as WorkerEvent
from celery.states import PENDING, RECEIVED
from sqlalchemy.exc import NoResultFound

from exporters import Exporter
from exporters.postgres.model import SessionManager
from exporters.postgres.model import Task as TaskModel
from utils import serialize_event

logger = daiquiri.getLogger(__name__)


class PostgresExporter(Exporter, Thread):
    event_fields = [
        "uuid",
        "state",
        "timestamp",
        "queue",
        "runtime",
        "name",
        "args",
        "kwargs",
        "hostname",
        "pid",
    ]

    def __init__(self, dburi=None):
        Thread.__init__(self)
        self.daemon = True
        self.queue = Queue()
        self.session = SessionManager().session_factory(dburi)

    def process_event(self, event: Union[TaskEvent, WorkerEvent]):
        self.queue.put(
            {
                "uuid": event.uuid,
                "status": event.state,
                **serialize_event(event, event_fields=self.event_fields),
            }
        )

    @staticmethod
    def to_model_dict(event_dict):
        status = event_dict["status"]
        model_dict = {
            "task_id": event_dict["uuid"],
            "current_status": event_dict["status"],
            "last_event_timestamp": datetime.fromtimestamp(event_dict["timestamp"]),
        }
        if status == PENDING:
            model_dict = {"queue": event_dict["queue"], **model_dict}
        if status in (PENDING, RECEIVED):
            model_dict = {
                "name": event_dict["name"],
                "args": list(eval(event_dict["args"])),
                "kwargs": json.loads(event_dict["kwargs"]),
                "worker": event_dict["hostname"],
                **model_dict,
            }
        return model_dict

    def run(self) -> None:
        logger.info("Starting Postgres exporter")
        while True:
            try:
                if self.queue.empty():
                    sleep(10)
                    continue
                event_dict = self.queue.get()
                print(event_dict)
                model_dict = self.to_model_dict(event_dict)
                task_id = model_dict["task_id"]
                try:
                    task = (
                        self.session.query(TaskModel).filter_by(task_id=task_id).one()
                    )
                except NoResultFound:
                    task = TaskModel(task_id=task_id)
                task.update_field(model_dict)
                self.session.add(task)
                self.session.commit()
            except Exception:
                logger.exception("postgres exporter exception")
                sleep(10)
