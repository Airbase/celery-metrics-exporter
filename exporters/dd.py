import logging
from enum import Enum
from threading import Thread
from time import sleep

from celery.states import FAILURE, PENDING, STARTED, SUCCESS
from datadog import initialize, statsd

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DataDogMetrics(Enum):
    TASK_WAIT_TIME = "celery.task.wait_time"
    TASK_RUNTIME_TIME = "celery.task.run_time"
    TOTAL_SUCCESS = "celery.task.success_count"
    TOTAL_FAILED = "celery.task.fail_count"


class DataDogSummary:  # maybe this can be generic
    def __init__(self, events):
        self.events = events

    @property
    def wait_time(self):
        """
        Returns wait time in seconds

        :return: int
        """
        client_sent_time = self.events[PENDING]["timestamp"]
        start_time = self.events[STARTED]["timestamp"]
        return start_time - client_sent_time

    @property
    def run_time(self):
        """
        Returns runtime in seconds

        :return: int
        """
        try:
            return self.events[SUCCESS]["runtime"]
        except KeyError:
            logger.exception(f"KeyError for {self.events}")
            return 0


class DataDogExporter(Thread):
    def __init__(self, api_key, config_option=None, store=None):
        Thread.__init__(self)
        self.daemon = True
        self.store = store
        self.api_key = api_key
        self.config_option = config_option or {
            "statsd_host": "127.0.0.1",
            "statsd_port": 8125,
        }
        initialize(**self.config_option)

    @staticmethod
    def get_tags(events):
        pending_event = events[PENDING]
        return {
            "queue": pending_event.get("queue", ""),
            "task_name": pending_event.get("name", ""),
        }

    def run(self) -> None:
        logger.info(f"Starting Datadog exporter")
        while True:
            try:
                if self.store.is_empty():
                    sleep(10)
                    continue
                task_id = self.store.get_processable_task()
                events = self.store.get_events(task_id)
                tags = self.get_tags(events)
                summary = DataDogSummary(events)
                statsd.histogram(
                    DataDogMetrics.TASK_WAIT_TIME, summary.wait_time, tags=tags
                )
                statsd.histogram(
                    DataDogMetrics.TASK_RUNTIME_TIME, summary.run_time, tags=tags
                )
                if SUCCESS in events:
                    statsd.increment(DataDogMetrics.TOTAL_SUCCESS, tags=tags)
                if FAILURE in events:
                    statsd.increment(DataDogMetrics.TOTAL_FAILED, tags=tags)
                self.store.pop_task(task_id)
                print(
                    f"{DataDogMetrics.TASK_WAIT_TIME.value}, {summary.wait_time}, {tags}"
                )
                print(
                    f"{DataDogMetrics.TASK_RUNTIME_TIME.value}, {summary.run_time}, {tags}"
                )
            except Exception as ex:
                logger.exception(f"datadog exporter exception {ex}")
                sleep(10)