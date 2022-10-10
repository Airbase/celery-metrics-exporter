from datetime import datetime

import daiquiri
import sqlalchemy as sa
from celery.states import PENDING
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

logger = daiquiri.getLogger(__name__)
ResultModelBase = declarative_base()


class Task(ResultModelBase):
    """Task result/status."""

    __tablename__ = "celery_task"

    id = sa.Column(
        sa.Integer,
        sa.Sequence("task_id_sequence"),
        primary_key=True,
        autoincrement=True,
    )
    task_id = sa.Column(sa.String(155), unique=True)
    current_status = sa.Column(sa.String(50), default=PENDING)
    last_event_timestamp = sa.Column(sa.DateTime)
    date_done = sa.Column(
        sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True
    )

    name = sa.Column(sa.String(155), nullable=True)
    args = sa.Column(JSONB, nullable=True)
    kwargs = sa.Column(JSONB, nullable=True)
    worker = sa.Column(sa.String(155), nullable=True)
    queue = sa.Column(sa.String(155), nullable=True)

    def __init__(self, task_id):
        self.task_id = task_id

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "result": self.result,
            "traceback": self.traceback,
            "date_done": self.date_done,
            "name": self.name,
            "args": self.args,
            "kwargs": self.kwargs,
            "worker": self.worker,
            "queue": self.queue,
        }

    def update_field(self, model_dict):
        for k, v in model_dict.items():
            setattr(self, k, v)

    def __repr__(self):
        return "<Task {0.task_id} state: {0.current_status}>".format(self)


class SessionManager:
    """Manage SQLAlchemy sessions."""

    def create_session(self, dburi, **kwargs):
        engine = create_engine(dburi, poolclass=NullPool, **kwargs)
        return engine, sessionmaker(bind=engine)

    def session_factory(self, dburi, **kwargs):
        engine, session = self.create_session(dburi, **kwargs)
        ResultModelBase.metadata.create_all(engine)
        return session()
