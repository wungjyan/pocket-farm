"""add user preferred farm

Revision ID: c3e7f9a1b2d4
Revises: a7b8c9d0e1f2
Create Date: 2026-09-02 15:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "c3e7f9a1b2d4"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("preferred_farm_id", mysql.BIGINT(unsigned=True), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_users_preferred_farm_id_farms"),
        "users",
        "farms",
        ["preferred_farm_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_users_preferred_farm_id"),
        "users",
        ["preferred_farm_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_preferred_farm_id"), table_name="users")
    op.drop_constraint(op.f("fk_users_preferred_farm_id_farms"), "users", type_="foreignkey")
    op.drop_column("users", "preferred_farm_id")
