"""Initiale Migration – vollständiges Schema aus Phase 0

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(200), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_table(
        "values",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
        sa.Column("risk_weight", sa.Integer, nullable=False, server_default="1"),
        sa.Column("allowed", sa.Boolean, nullable=False, server_default="1"),
        sa.Column("vtype", sa.String(20), nullable=False, server_default="string"),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_table(
        "generations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("strategy", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("coverage_meta", sa.Text, nullable=True),
    )
    op.create_table(
        "testcases",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("generation_id", sa.Integer, sa.ForeignKey("generations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
    )
    op.create_table(
        "testcase_values",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("testcase_id", sa.Integer, sa.ForeignKey("testcases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("value", sa.String(500), nullable=False),
    )
    op.create_table(
        "rules",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(20), nullable=False, server_default="dependency"),
        sa.Column("if_category_id", sa.Integer, sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("if_value", sa.String, nullable=False),
        sa.Column("then_category_id", sa.Integer, sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("then_value", sa.String, nullable=False),
        sa.Column("then_values_json", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("rules")
    op.drop_table("testcase_values")
    op.drop_table("testcases")
    op.drop_table("generations")
    op.drop_table("values")
    op.drop_table("categories")
    op.drop_table("projects")
