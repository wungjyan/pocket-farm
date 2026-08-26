"""add production plot status species index

Revision ID: e9a5f8d2b7c4
Revises: c4d7e2f9a561
Create Date: 2026-08-26 16:20:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e9a5f8d2b7c4"
down_revision: Union[str, Sequence[str], None] = "c4d7e2f9a561"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_productions_plot_status_species",
        "productions",
        ["plot_id", "status", "species_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_productions_plot_status_species", table_name="productions")
