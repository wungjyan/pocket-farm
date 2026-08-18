"""create plots

Revision ID: 6c41d1c6b6f1
Revises: 9c8d9c86e54a
Create Date: 2026-08-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "6c41d1c6b6f1"
down_revision: Union[str, Sequence[str], None] = "9c8d9c86e54a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plots",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("farm_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=True),
        sa.Column("area_value", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("area_unit", sa.String(length=20), nullable=True),
        sa.Column("area_m2", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("boundary", mysql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["farm_id"], ["farms.id"], name=op.f("fk_plots_farm_id_farms"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_plots")),
    )
    op.create_index(op.f("ix_plots_farm_id"), "plots", ["farm_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_plots_farm_id"), table_name="plots")
    op.drop_table("plots")
