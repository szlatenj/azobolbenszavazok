"""Help requests and carpools tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "voting_guide_help_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("voting_method", sa.String(20), nullable=False),
        sa.Column("language_pref", sa.String(2), server_default="hu"),
        sa.Column("submitted_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("is_read", sa.Boolean, server_default=sa.text("false")),
    )

    op.create_table(
        "voting_guide_carpools",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("carpool_type", sa.String(10), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("starting_location", sa.String(500), nullable=False),
        sa.Column("seats", sa.Integer, nullable=True),
        sa.Column("voting_method", sa.String(20), nullable=False),
        sa.Column("language_pref", sa.String(2), server_default="hu"),
        sa.Column("submitted_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("ip_address", sa.String(45), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("voting_guide_carpools")
    op.drop_table("voting_guide_help_requests")
