"""Create task_id_sequence table

Revision ID: a6264519d817
Revises: de20bf8510b0
Create Date: 2022-10-07 20:20:51.960276

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.schema import CreateSequence, DropSequence, Sequence

# revision identifiers, used by Alembic.
revision = "a6264519d817"
down_revision = "de20bf8510b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # this was manually generated, since alembic didn't auto-generate it
    op.execute(CreateSequence(Sequence("task_id_sequence")))
    op.alter_column(
        "celery_task",
        "id",
        nullable=False,
        server_default=sa.text("nextval('task_id_sequence'::regclass)"),
    )


def downgrade() -> None:
    op.execute(DropSequence(Sequence("task_id_sequence")))
