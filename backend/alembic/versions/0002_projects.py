"""progetti: tabella projects + epics.project_id

Introduce il contenitore di primo livello "progetto" (Jira o interno).
Le epiche esistenti vengono assegnate a un progetto interno di default.

Revision ID: 0002_projects
Revises: 0001_init
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

from db import IS_POSTGRES, SCHEMA

revision = "0002_projects"
down_revision = "0001_init"
branch_labels = None
depends_on = None

# NB: a differenza di create_table, le operazioni ALTER/INSERT di Alembic non
# applicano lo schema_translate_map (None -> "tabula") impostato in env.py, quindi
# qui lo schema `tabula` va indicato esplicitamente con schema=SCHEMA.

_DEFAULT_ID = "pdefault0"  # id stabile del progetto di default


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), server_default="internal", nullable=False),
        sa.Column("jira_key", sa.String(), server_default="", nullable=True),
        schema=SCHEMA,
    )

    # 1) colonna inizialmente nullable per poter fare il backfill
    op.add_column("epics", sa.Column("project_id", sa.String(), nullable=True), schema=SCHEMA)

    # 2) progetto interno di default per le epiche preesistenti
    projects = sa.table(
        "projects",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("type", sa.String),
        sa.column("jira_key", sa.String),
        schema=SCHEMA,
    )
    op.bulk_insert(
        projects,
        [{"id": _DEFAULT_ID, "name": "Default", "type": "internal", "jira_key": ""}],
    )

    # 3) backfill: tutte le epiche esistenti al progetto di default
    epics = sa.table("epics", sa.column("project_id", sa.String), schema=SCHEMA)
    op.execute(epics.update().values(project_id=_DEFAULT_ID))

    # 4) ora la colonna può diventare NOT NULL + vincolo FK.
    #    SQLite non supporta ALTER per NOT NULL/FK: si usa il batch mode (ricrea
    #    la tabella). Su Postgres l'ALTER nativo è sufficiente.
    if IS_POSTGRES:
        op.alter_column("epics", "project_id", nullable=False, schema=SCHEMA)
        op.create_foreign_key(
            "fk_epics_project_id",
            "epics",
            "projects",
            ["project_id"],
            ["id"],
            source_schema=SCHEMA,
            referent_schema=SCHEMA,
            ondelete="CASCADE",
        )
    else:
        with op.batch_alter_table("epics", schema=SCHEMA) as batch:
            batch.alter_column("project_id", nullable=False)
            batch.create_foreign_key(
                "fk_epics_project_id",
                "projects",
                ["project_id"],
                ["id"],
                ondelete="CASCADE",
            )


def downgrade() -> None:
    if IS_POSTGRES:
        op.drop_constraint("fk_epics_project_id", "epics", schema=SCHEMA, type_="foreignkey")
        op.drop_column("epics", "project_id", schema=SCHEMA)
    else:
        with op.batch_alter_table("epics", schema=SCHEMA) as batch:
            batch.drop_constraint("fk_epics_project_id", type_="foreignkey")
            batch.drop_column("project_id")
    op.drop_table("projects", schema=SCHEMA)
