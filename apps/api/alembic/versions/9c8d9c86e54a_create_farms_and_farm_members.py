"""create farms and farm members

Revision ID: 9c8d9c86e54a
Revises: f67d91555137
Create Date: 2026-08-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision: str = "9c8d9c86e54a"
down_revision: Union[str, Sequence[str], None] = "f67d91555137"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "farms",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("farm_code", sa.CHAR(length=6), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("created_by", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["created_by"], ["users.id"], name=op.f("fk_farms_created_by_users"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_farms")),
        sa.UniqueConstraint("farm_code", name=op.f("uq_farms_farm_code")),
    )
    op.create_table(
        "farm_members",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("farm_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["farm_id"], ["farms.id"], name=op.f("fk_farm_members_farm_id_farms"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_farm_members_user_id_users"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_farm_members")),
        sa.UniqueConstraint(
            "farm_id", "user_id", name="uq_farm_members_farm_id_user_id"
        ),
    )
    op.create_index(op.f("ix_farm_members_user_id"), "farm_members", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_farm_members_user_id"), table_name="farm_members")
    op.drop_table("farm_members")
    op.drop_table("farms")
