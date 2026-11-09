"""req_4001_4020_add_users_and_refresh_tokens_tables

Revision ID: req4001_4020_auth_tables
Revises: da53f00e5892
Create Date: 2026-10-05

REQ-4001: User-Modell mit Password-Hashing (argon2id)
REQ-4020: Rollen-Modell (Admin/Editor/Viewer)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "req4001_4020_auth_tables"
down_revision: Union[str, None] = "da53f00e5892"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create users and refresh_tokens tables for EPIC-18 Multi-User Auth."""

    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("is_first_admin", sa.Boolean(), nullable=False, server_default="0"),
        # REQ-4027 AK-10: Flag Standardpasswort aktiv
        sa.Column("default_password_active", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Refresh tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("token", sa.String(500), unique=True, nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Drop users and refresh_tokens tables."""
    op.drop_table("refresh_tokens")
    op.drop_table("users")