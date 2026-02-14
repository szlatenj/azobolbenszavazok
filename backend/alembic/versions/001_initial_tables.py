"""Initial voting guide tables

Revision ID: 001
Revises:
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "voting_guide_signups",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("voting_method", sa.String(20), nullable=False),
        sa.Column("language_pref", sa.String(2), server_default="hu"),
        sa.Column("signup_date", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_voting_guide_signups_email", "voting_guide_signups", ["email"])

    op.create_table(
        "voting_guide_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("language_pref", sa.String(2), server_default="hu"),
        sa.Column("submitted_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("is_read", sa.Boolean, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_table("voting_guide_contacts")
    op.drop_index("ix_voting_guide_signups_email", table_name="voting_guide_signups")
    op.drop_table("voting_guide_signups")
