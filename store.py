import logging
from abc import ABC, abstractmethod
from threading import Lock

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TaskStore(ABC):
    event_fields = ["uuid", "state", "timestamp", "queue", "runtime", "name"]

    @abstractmethod
    def is_empty(self):
        pass

    @abstractmethod
    def get_processable_task(self):
        pass

    @abstractmethod
    def get_events(self, task_id):
        pass

    @abstractmethod
    def pop_task(self, task_id):
        pass

    @abstractmethod
    def add_event(self, task_id, state, event):
        pass

    @abstractmethod
    def add_processable_task(self, task_id):
        pass

    def serialize(self, event):
        return {
            field: getattr(event, field)
            for field in self.event_fields
            if hasattr(event, field)
        }


class InMemoryStore(TaskStore):
    def __init__(self, event_store=None, processing_queue=None):
        self.event_store = event_store
        self.processing_queue = processing_queue
        self.mutex = Lock()

    def is_empty(self):
        return self.processing_queue.empty()

    def get_processable_task(self):
        return self.processing_queue.get()

    def get_events(self, task_id):
        return self.event_store.get(task_id)

    def pop_task(self, task_id):
        with self.mutex:
            self.event_store.data.pop(task_id)

    def add_event(self, task_id, state, event):
        event_dict = self.serialize(event)
        logger.debug(f"Serialized data: {event_dict}")
        try:
            self.event_store[task_id][state] = event_dict
        except KeyError:
            self.event_store[event.uuid] = {event.state: event_dict}

    def add_processable_task(self, task_id):
        self.processing_queue.put(task_id)
