from enum import Enum
from threading import Thread
from time import sleep

import daiquiri
from celery.events.state import Task, Worker
from celery.states import FAILURE, PENDING, READY_STATES, STARTED, SUCCESS
from datadog import initialize, statsd

from exporters import Exporter

logger = daiquiri.getLogger(__name__)


class DataDogMetrics(Enum):
    TASK_WAIT_TIME = "celery.task.wait_time"
    TASK_RUNTIME_TIME = "celery.task.run_time"
    TOTAL_SUCCESS = "celery.task.success_count"
    TOTAL_FAILED = "celery.task.fail_count"


class DataDogSummary:  # maybe this can be generic
    def __init__(self, events) -> None:
        self.events = events

    @property
    def wait_time(self):
        """Returns wait time of a task in seconds.

        Note:
        ----
            observation task started from celery-beat don't have pending or task-sent event

        Returns:
        -------
        int
            Wait Time in seconds

        """
        try:
            client_sent_time = self.events[PENDING]["timestamp"]
            start_time = self.events[STARTED]["timestamp"]
            return start_time - client_sent_time
        except KeyError:
            logger.exception(f"KeyError for {self.events}")
            return None

    @property
    def run_time(self):
        """Returns execution of a task in seconds.

        Returns
        -------
        int
            Run Time in seconds

        """
        try:
            return self.events[SUCCESS]["runtime"]
        except KeyError:
            logger.exception(f"KeyError for {self.events}")
            return None


class DataDogExporter(Exporter, Thread):
    def __init__(self, config_option=None, store=None) -> None:
        Thread.__init__(self)
        self.daemon = True
        self.store = store
        self.config_option = config_option or {
            "statsd_host": "127.0.0.1",
            "statsd_port": 8125,
        }
        initialize(**self.config_option)

    @staticmethod
    def get_tags(events):
        try:
            pending_event = events[PENDING]
            tags_dict = {
                "queue": pending_event.get("queue", ""),
                "task_name": pending_event.get("name", ""),
            }
            return [f"{key}:{value}" for key, value in tags_dict.items() if value]
        except KeyError:
            logger.exception(f"Pending Event missing in {events}")

    def process_event(self, event: Task | Worker) -> None:
        self.store.add_event(event.uuid, event.state, event)
        if event.state in READY_STATES:
            logger.debug(f"task: {event.uuid} ended with state: {event.state}")
            self.store.add_processable_task(event.uuid)

    def run(self) -> None:
        logger.info("Starting Datadog exporter")
        while True:
            try:
                if self.store.is_empty():
                    sleep(10)
                    continue
                task_id = self.store.get_processable_task()
                events = self.store.get_events(task_id)
                tags = self.get_tags(events)
                summary = DataDogSummary(events)
                if (wait_time := summary.wait_time) is not None:
                    statsd.histogram(
                        DataDogMetrics.TASK_WAIT_TIME.value,
                        wait_time,
                        tags=tags,
                    )
                if (run_time := summary.run_time) is not None:
                    statsd.histogram(
                        DataDogMetrics.TASK_RUNTIME_TIME.value,
                        run_time,
                        tags=tags,
                    )
                if SUCCESS in events:
                    statsd.increment(DataDogMetrics.TOTAL_SUCCESS.value, tags=tags)
                if FAILURE in events:
                    statsd.increment(DataDogMetrics.TOTAL_FAILED.value, tags=tags)
                self.store.pop_task(task_id)
            except Exception:
                logger.exception("datadog exporter exception")
                sleep(10)
