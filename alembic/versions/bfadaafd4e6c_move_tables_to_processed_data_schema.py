"""move tables to processed_data schema

Revision ID: bfadaafd4e6c
Revises: 1ae9bb194cfa
Create Date: 2026-02-18 18:43:55.635508

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfadaafd4e6c'
down_revision: Union[str, Sequence[str], None] = '1ae9bb194cfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE raw_data.provider SET SCHEMA core"
    )

    op.execute(
        "ALTER TABLE raw_data.run SET SCHEMA core"
    )

    op.execute(
        "ALTER TABLE raw_data.raw_data SET SCHEMA processed_data"
    )

    op.execute(
        "ALTER TABLE processed_data.raw_data RENAME TO processed_data"
    )

def downgrade() -> None:
    op.execute(
        "ALTER TABLE processed_data.processed_data RENAME TO raw_data"
    )

    op.execute(
        "ALTER TABLE core.provider SET SCHEMA raw_data"
    )

    op.execute(
        "ALTER TABLE core.run SET SCHEMA raw_data"
    )

    op.execute(
        "ALTER TABLE processed_data.raw_data SET SCHEMA raw_data"
    )