"""Creating response table

Revision ID: 0a8cb28dc397
Revises: b5c8e1cfcb42
Create Date: 2023-11-22 12:27:50.848006

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a8cb28dc397"
down_revision: Union[str, None] = "b5c8e1cfcb42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table("response")
    op.add_column(
        "response",
        sa.Column("interaction_id", sa.String(), primary_key=True, nullable=False),
    )
    op.add_column("response", sa.Column("response_id", sa.String(), nullable=False))
    op.add_column("response", sa.Column("survey_id", sa.String(), nullable=False))
    op.add_column("response", sa.Column("session_id", sa.String(), nullable=False))
    op.add_column("response", sa.Column("dist", sa.String(), nullable=False))


def downgrade() -> None:
    op.drop_column("response", "interaction_id")
    op.drop_column("response", "response_id")
    op.drop_column("response", "survey_id")
    op.drop_column("response", "session_id")
    op.drop_column("response", "dist")
    op.drop_table("response")
