"""manage operation types

Revision ID: 54698bd6b5f1
Revises: 2c972e3fc98e
Create Date: 2026-08-19 15:49:54.550683

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '54698bd6b5f1'
down_revision: Union[str, Sequence[str], None] = '2c972e3fc98e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operation_types",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("sort_order", mysql.INTEGER(unsigned=True), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_operation_types")),
        sa.UniqueConstraint("code", name=op.f("uq_operation_types_code")),
    )
    op.create_index(op.f("ix_operation_types_status"), "operation_types", ["status"], unique=False)

    operation_types = sa.table(
        "operation_types",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("status", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )
    now = datetime(2026, 8, 19)
    op.bulk_insert(
        operation_types,
        [
            {"code": "FERTILIZE", "name": "施肥", "status": "ACTIVE", "sort_order": 10, "created_at": now, "updated_at": now},
            {"code": "PLOW", "name": "翻耕", "status": "ACTIVE", "sort_order": 20, "created_at": now, "updated_at": now},
            {"code": "RIDGE", "name": "起垄", "status": "ACTIVE", "sort_order": 30, "created_at": now, "updated_at": now},
            {"code": "PESTICIDE", "name": "用药", "status": "ACTIVE", "sort_order": 40, "created_at": now, "updated_at": now},
            {"code": "IRRIGATE", "name": "灌溉", "status": "ACTIVE", "sort_order": 50, "created_at": now, "updated_at": now},
            {"code": "WEED", "name": "除草", "status": "ACTIVE", "sort_order": 60, "created_at": now, "updated_at": now},
            {"code": "PRUNE", "name": "修剪", "status": "ACTIVE", "sort_order": 70, "created_at": now, "updated_at": now},
            {"code": "FEED", "name": "喂料", "status": "ACTIVE", "sort_order": 80, "created_at": now, "updated_at": now},
            {"code": "DISINFECT", "name": "消毒", "status": "ACTIVE", "sort_order": 90, "created_at": now, "updated_at": now},
            {"code": "CLEAN_MANURE", "name": "清粪", "status": "ACTIVE", "sort_order": 100, "created_at": now, "updated_at": now},
            {"code": "BREED", "name": "配种", "status": "ACTIVE", "sort_order": 110, "created_at": now, "updated_at": now},
            {"code": "FEED_FISH", "name": "投料", "status": "ACTIVE", "sort_order": 120, "created_at": now, "updated_at": now},
            {"code": "CHANGE_WATER", "name": "换水", "status": "ACTIVE", "sort_order": 130, "created_at": now, "updated_at": now},
            {"code": "CLEAN_POND", "name": "清塘", "status": "ACTIVE", "sort_order": 140, "created_at": now, "updated_at": now},
            {"code": "MEASURE_TEMP", "name": "测水温", "status": "ACTIVE", "sort_order": 150, "created_at": now, "updated_at": now},
        ],
    )

    op.add_column(
        "farm_operations",
        sa.Column("operation_type_id", mysql.BIGINT(unsigned=True), nullable=True),
    )
    op.execute(
        """
        UPDATE farm_operations
        JOIN operation_types ON operation_types.code = farm_operations.operation_type
        SET farm_operations.operation_type_id = operation_types.id
        """
    )
    op.alter_column(
        "farm_operations",
        "operation_type_id",
        existing_type=mysql.BIGINT(unsigned=True),
        nullable=False,
    )
    op.create_index(
        op.f("ix_farm_operations_operation_type_id"),
        "farm_operations",
        ["operation_type_id"],
        unique=False,
    )
    op.create_foreign_key(
        op.f("fk_farm_operations_operation_type_id_operation_types"),
        "farm_operations",
        "operation_types",
        ["operation_type_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_column("farm_operations", "operation_type")


def downgrade() -> None:
    op.add_column(
        "farm_operations",
        sa.Column("operation_type", mysql.VARCHAR(length=30), nullable=True),
    )
    op.execute(
        """
        UPDATE farm_operations
        JOIN operation_types ON operation_types.id = farm_operations.operation_type_id
        SET farm_operations.operation_type = operation_types.code
        """
    )
    op.alter_column(
        "farm_operations",
        "operation_type",
        existing_type=mysql.VARCHAR(length=30),
        nullable=False,
    )
    op.drop_constraint(
        op.f("fk_farm_operations_operation_type_id_operation_types"),
        "farm_operations",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_farm_operations_operation_type_id"), table_name="farm_operations")
    op.drop_column("farm_operations", "operation_type_id")
    op.drop_index(op.f("ix_operation_types_status"), table_name="operation_types")
    op.drop_table("operation_types")
