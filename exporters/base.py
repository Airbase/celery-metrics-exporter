from abc import ABC, abstractmethod
from typing import Union

from celery.events.state import Task, Worker


class Exporter(ABC):
    @abstractmethod
    def process_event(self, event: Union[Task, Worker]):
        pass
