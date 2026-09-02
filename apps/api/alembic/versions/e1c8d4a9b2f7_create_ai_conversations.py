"""create ai conversations

Revision ID: e1c8d4a9b2f7
Revises: d5f8a2c4e6b9
Create Date: 2026-09-02 16:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "e1c8d4a9b2f7"
down_revision: Union[str, Sequence[str], None] = "d5f8a2c4e6b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_conversations",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("user_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("farm_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["farm_id"], ["farms.id"], name=op.f("fk_ai_conversations_farm_id_farms"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_ai_conversations_user_id_users"), ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_conversations")),
    )
    op.create_index(
        "ix_ai_conversations_user_farm_updated",
        "ai_conversations",
        ["user_id", "farm_id", "updated_at"],
        unique=False,
    )
    op.create_table(
        "ai_messages",
        sa.Column("id", mysql.BIGINT(unsigned=True), autoincrement=True, nullable=False),
        sa.Column("conversation_id", mysql.BIGINT(unsigned=True), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("references", sa.JSON(), nullable=True),
        sa.Column("candidates", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["ai_conversations.id"],
            name=op.f("fk_ai_messages_conversation_id_ai_conversations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_messages")),
    )
    op.create_index(
        "ix_ai_messages_conversation_id_id",
        "ai_messages",
        ["conversation_id", "id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_ai_messages_conversation_id_id", table_name="ai_messages")
    op.drop_table("ai_messages")
    op.drop_index("ix_ai_conversations_user_farm_updated", table_name="ai_conversations")
    op.drop_table("ai_conversations")
