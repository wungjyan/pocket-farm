"""add lettuce species

Revision ID: c4d7e2f9a561
Revises: b8e4d2a1c673
Create Date: 2026-08-20 15:30:00.000000

"""

from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c4d7e2f9a561"
down_revision: Union[str, Sequence[str], None] = "b8e4d2a1c673"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    species = sa.table(
        "species",
        sa.column("name", sa.String),
        sa.column("industry", sa.String),
        sa.column("individual_unit", sa.String),
        sa.column("created_at", sa.DateTime),
    )
    op.bulk_insert(
        species,
        [
            {
                "name": "生菜",
                "industry": "AGRICULTURE",
                "individual_unit": "PLANT",
                "created_at": datetime(2026, 8, 20),
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM species WHERE name = '生菜' AND industry = 'AGRICULTURE'"
    )
