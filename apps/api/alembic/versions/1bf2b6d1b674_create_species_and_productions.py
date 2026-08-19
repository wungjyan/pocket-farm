"""create species and productions

Revision ID: 1bf2b6d1b674
Revises: 6c41d1c6b6f1
Create Date: 2026-08-19 11:03:11.092748

"""
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "1bf2b6d1b674"
down_revision: Union[str, Sequence[str], None] = "6c41d1c6b6f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "species",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("industry", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_species")),
    )
    op.create_index(op.f("ix_species_industry"), "species", ["industry"], unique=False)
    species_table = sa.table(
        "species",
        sa.column("name", sa.String),
        sa.column("industry", sa.String),
        sa.column("created_at", sa.DateTime),
    )
    created_at = datetime(2026, 8, 19)
    op.bulk_insert(
        species_table,
        [
            {"name": "水稻", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "小麦", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "玉米", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "大豆", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "黄瓜", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "番茄", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "辣椒", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "马铃薯", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "葡萄", "industry": "AGRICULTURE", "created_at": created_at},
            {"name": "杉木", "industry": "FORESTRY", "created_at": created_at},
            {"name": "松树", "industry": "FORESTRY", "created_at": created_at},
            {"name": "毛竹", "industry": "FORESTRY", "created_at": created_at},
            {"name": "猪", "industry": "LIVESTOCK", "created_at": created_at},
            {"name": "牛", "industry": "LIVESTOCK", "created_at": created_at},
            {"name": "羊", "industry": "LIVESTOCK", "created_at": created_at},
            {"name": "鸡", "industry": "LIVESTOCK", "created_at": created_at},
            {"name": "鸭", "industry": "LIVESTOCK", "created_at": created_at},
            {"name": "青鱼", "industry": "FISHERY", "created_at": created_at},
            {"name": "草鱼", "industry": "FISHERY", "created_at": created_at},
            {"name": "鲤鱼", "industry": "FISHERY", "created_at": created_at},
            {"name": "鲫鱼", "industry": "FISHERY", "created_at": created_at},
            {"name": "鲈鱼", "industry": "FISHERY", "created_at": created_at},
            {"name": "小龙虾", "industry": "FISHERY", "created_at": created_at},
        ],
    )
    op.create_table(
        "productions",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("plot_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("species_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("variety", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_on", sa.Date(), nullable=False),
        sa.Column("ended_on", sa.Date(), nullable=True),
        sa.Column("planting_standard", sa.String(length=20), nullable=True),
        sa.Column("planting_method", sa.String(length=20), nullable=True),
        sa.Column("work_method", sa.String(length=20), nullable=False),
        sa.Column("expected_harvest_on", sa.Date(), nullable=True),
        sa.Column("expected_yield", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("expected_yield_unit", sa.String(length=20), nullable=True),
        sa.Column("initial_quantity", sa.Numeric(precision=14, scale=4), nullable=True),
        sa.Column("initial_quantity_unit", sa.String(length=20), nullable=True),
        sa.Column("plant_spacing", sa.String(length=100), nullable=True),
        sa.Column("entry_age_days", mysql.INTEGER(unsigned=True), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["plot_id"],
            ["plots.id"],
            name=op.f("fk_productions_plot_id_plots"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["species_id"],
            ["species.id"],
            name=op.f("fk_productions_species_id_species"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_productions")),
    )
    op.create_index(op.f("ix_productions_plot_id"), "productions", ["plot_id"], unique=False)
    op.create_index(op.f("ix_productions_species_id"), "productions", ["species_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_productions_species_id"), table_name="productions")
    op.drop_index(op.f("ix_productions_plot_id"), table_name="productions")
    op.drop_table("productions")
    op.drop_index(op.f("ix_species_industry"), table_name="species")
    op.drop_table("species")
