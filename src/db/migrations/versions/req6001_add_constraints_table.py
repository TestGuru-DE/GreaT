"""req_6001_add_constraints_table

Revision ID: req6001_constraints_table
Revises: req4001_4020_auth_tables
Create Date: 2026-11-18

REQ-6001: Logische Constraints (Mehrbedingungs-Regeln)
Neue Tabelle 'constraints' fuer JSON-AST-basierte Constraints.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "req6001_constraints_table"
down_revision: Union[str, None] = "req4001_4020_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "constraints",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("kind", sa.String(10), nullable=False),  # forbid | implies
        sa.Column("expression_json", sa.Text(), nullable=False),  # JSON-AST
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "last_modified_by",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("last_modified_at", sa.DateTime(), nullable=True),
    )
    # Index fuer project_id (schnelles Lookup)
    op.create_index(op.f("ix_constraints_project_id"), "constraints", ["project_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_constraints_project_id"), table_name="constraints")
    op.drop_table("constraints")