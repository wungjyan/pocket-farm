"""merge ai and production heads

Revision ID: a7b8c9d0e1f2
Revises: ebab87a2e453, f1a2b3c4d5e6
Create Date: 2026-09-02 12:05:00.000000

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = ("ebab87a2e453", "f1a2b3c4d5e6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
