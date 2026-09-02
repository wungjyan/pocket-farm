"""add ai farm settings and daily usage

Revision ID: f1a2b3c4d5e6
Revises: e9a5f8d2b7c4
Create Date: 2026-09-02 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e9a5f8d2b7c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "farms",
        sa.Column("ai_enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.create_table(
        "ai_daily_turn_usages",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("turn_count", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_ai_daily_turn_usages_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_daily_turn_usages")),
        sa.UniqueConstraint(
            "user_id",
            "usage_date",
            name="uq_ai_daily_turn_usages_user_id_usage_date",
        ),
    )


def downgrade() -> None:
    op.drop_table("ai_daily_turn_usages")
    op.drop_column("farms", "ai_enabled")
