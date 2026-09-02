"""drop preferred farm foreign key

Revision ID: d5f8a2c4e6b9
Revises: c3e7f9a1b2d4
Create Date: 2026-09-02 15:45:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5f8a2c4e6b9"
down_revision: Union[str, Sequence[str], None] = "c3e7f9a1b2d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(op.f("fk_users_preferred_farm_id_farms"), "users", type_="foreignkey")


def downgrade() -> None:
    op.create_foreign_key(
        op.f("fk_users_preferred_farm_id_farms"),
        "users",
        "farms",
        ["preferred_farm_id"],
        ["id"],
        ondelete="SET NULL",
    )
