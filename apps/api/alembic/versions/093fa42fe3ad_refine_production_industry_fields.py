"""refine production industry fields

Revision ID: 093fa42fe3ad
Revises: 1bf2b6d1b674
Create Date: 2026-08-19 14:13:02.560152

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "093fa42fe3ad"
down_revision: Union[str, Sequence[str], None] = "1bf2b6d1b674"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "productions",
        sa.Column("expected_yield_per_mu", sa.Numeric(precision=14, scale=4), nullable=True),
    )
    op.add_column(
        "productions",
        sa.Column("plant_spacing_cm", sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.alter_column(
        "productions",
        "work_method",
        existing_type=mysql.VARCHAR(length=20),
        nullable=True,
    )
    op.drop_column("productions", "expected_yield")
    op.drop_column("productions", "expected_yield_unit")
    op.drop_column("productions", "initial_quantity_unit")
    op.drop_column("productions", "plant_spacing")

    op.add_column("species", sa.Column("individual_unit", sa.String(length=20), nullable=True))
    op.execute(
        """
        UPDATE species
        SET individual_unit = CASE
            WHEN industry IN ('AGRICULTURE', 'FORESTRY') THEN 'PLANT'
            WHEN name IN ('鸡', '鸭') THEN 'FEATHER'
            WHEN industry = 'LIVESTOCK' THEN 'HEAD'
            WHEN industry = 'FISHERY' THEN 'TAIL'
            ELSE 'PIECE'
        END
        """
    )
    op.alter_column(
        "species",
        "individual_unit",
        existing_type=mysql.VARCHAR(length=20),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("species", "individual_unit")
    op.add_column("productions", sa.Column("plant_spacing", mysql.VARCHAR(length=100), nullable=True))
    op.add_column(
        "productions",
        sa.Column("initial_quantity_unit", mysql.VARCHAR(length=20), nullable=True),
    )
    op.add_column(
        "productions",
        sa.Column("expected_yield_unit", mysql.VARCHAR(length=20), nullable=True),
    )
    op.add_column(
        "productions",
        sa.Column("expected_yield", mysql.DECIMAL(precision=14, scale=4), nullable=True),
    )
    op.execute("UPDATE productions SET work_method = 'MANUAL' WHERE work_method IS NULL")
    op.alter_column(
        "productions",
        "work_method",
        existing_type=mysql.VARCHAR(length=20),
        nullable=False,
    )
    op.drop_column("productions", "plant_spacing_cm")
    op.drop_column("productions", "expected_yield_per_mu")
