"""init tabula schema (epics, agents, stories, tasks) con md/phase

Revision ID: 0001_init
Revises:
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

# Lo schema è applicato via schema_translate_map (None -> "tabula") in env.py,
# quindi qui le tabelle non specificano lo schema.


def upgrade() -> None:
    op.create_table(
        "epics",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("desc", sa.Text(), server_default="", nullable=True),
        sa.Column("status", sa.String(), server_default="todo", nullable=False),
        sa.Column("md", sa.Text(), server_default="", nullable=True),
        sa.Column("md_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "agents",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("current_task", sa.String(), server_default="Inattivo", nullable=True),
        sa.Column("status", sa.String(), server_default="idle", nullable=False),
        sa.Column("tokens", sa.Integer(), server_default="0", nullable=False),
    )
    op.create_table(
        "stories",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("desc", sa.Text(), server_default="", nullable=True),
        sa.Column("status", sa.String(), server_default="todo", nullable=False),
        sa.Column("phase", sa.String(), server_default="analysis", nullable=False),
        sa.Column("epic_id", sa.String(), nullable=False),
        sa.Column("md", sa.Text(), server_default="", nullable=True),
        sa.Column("md_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["epic_id"], ["epics.id"], ondelete="CASCADE"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("status", sa.String(), server_default="todo", nullable=False),
        sa.Column("story_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=True),
        sa.Column("md", sa.Text(), server_default="", nullable=True),
        sa.Column("md_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["story_id"], ["stories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    op.drop_table("tasks")
    op.drop_table("stories")
    op.drop_table("agents")
    op.drop_table("epics")
