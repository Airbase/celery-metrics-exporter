from abc import ABC, abstractmethod

from celery.events.state import Task, Worker


class Exporter(ABC):
    @abstractmethod
    def process_event(self, event: Task | Worker):
        pass
