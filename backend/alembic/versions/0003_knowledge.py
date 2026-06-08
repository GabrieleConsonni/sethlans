"""profilo progetto + knowledge cards

Aggiunge a `projects` il profilo consultabile (md/md_updated_at) e i puntatori
strutturati per-ruolo (config JSON), e introduce la tabella `knowledge`: le card
di conoscenza di progetto prodotte/consumate dal pre-training (`/sethlans-onboard`).

Revision ID: 0003_knowledge
Revises: 0002_projects
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa

from db import SCHEMA

revision = "0003_knowledge"
down_revision = "0002_projects"
branch_labels = None
depends_on = None

# NB: come in 0002, le operazioni ALTER non applicano lo schema_translate_map
# impostato in env.py: lo schema `tabula` va indicato esplicitamente con schema=SCHEMA.


def upgrade() -> None:
    # 1) profilo + config sui progetti esistenti
    op.add_column("projects", sa.Column("md", sa.Text(), server_default="", nullable=False), schema=SCHEMA)
    op.add_column("projects", sa.Column("md_updated_at", sa.DateTime(timezone=True), nullable=True), schema=SCHEMA)
    op.add_column(
        "projects",
        sa.Column("config", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        schema=SCHEMA,
    )

    # 2) card di conoscenza
    op.create_table(
        "knowledge",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), server_default="general", nullable=False),
        sa.Column("kind", sa.String(), server_default="kb", nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source", sa.String(), server_default="manual", nullable=False),
        sa.Column("md", sa.Text(), server_default="", nullable=False),
        sa.Column("md_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"], [f"{SCHEMA}.projects.id"], ondelete="CASCADE"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_knowledge_project_id", "knowledge", ["project_id"], schema=SCHEMA
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_project_id", table_name="knowledge", schema=SCHEMA)
    op.drop_table("knowledge", schema=SCHEMA)
    op.drop_column("projects", "config", schema=SCHEMA)
    op.drop_column("projects", "md_updated_at", schema=SCHEMA)
    op.drop_column("projects", "md", schema=SCHEMA)
