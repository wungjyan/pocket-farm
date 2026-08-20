"""create harvest records

Revision ID: b8e4d2a1c673
Revises: 54698bd6b5f1
Create Date: 2026-08-20 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "b8e4d2a1c673"
down_revision: Union[str, Sequence[str], None] = "54698bd6b5f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "harvest_records",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("production_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=14, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("work_method", sa.String(length=20), nullable=False),
        sa.Column("harvested_at", sa.DateTime(), nullable=False),
        sa.Column("operator_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("created_by", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("product_name", sa.String(length=100), nullable=True),
        sa.Column("grade", sa.String(length=100), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_harvest_records_created_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["operator_id"],
            ["users.id"],
            name=op.f("fk_harvest_records_operator_id_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["production_id"],
            ["productions.id"],
            name=op.f("fk_harvest_records_production_id_productions"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_harvest_records")),
    )
    op.create_index(
        op.f("ix_harvest_records_operator_id"),
        "harvest_records",
        ["operator_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_harvest_records_production_id"),
        "harvest_records",
        ["production_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_harvest_records_production_id"), table_name="harvest_records")
    op.drop_index(op.f("ix_harvest_records_operator_id"), table_name="harvest_records")
    op.drop_table("harvest_records")
