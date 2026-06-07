"""
Alembic env per Tabula — single-tenant, schema dedicato `tabula`.
Mirror semplificato del pattern schema-scoped di quality-flow:
- crea lo schema `tabula` se assente;
- traduce lo schema implicito dei modelli su `tabula` (schema_translate_map);
- version table e tabelle confinate nello schema `tabula`.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import create_engine, pool, text

# rende importabili models.py / db.py (cartella backend)
sys.path.append(str(Path(__file__).resolve().parents[1]))

from db import SCHEMA, TABULA_DB_URL  # noqa: E402
from models import Base  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):
    # considera solo le tabelle dello schema 'tabula' (schema implicito = None)
    if type_ == "table" and object.schema not in (None, SCHEMA):
        return False
    return True


def _create_schema(connection):
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}"))


def run_migrations_offline() -> None:
    context.configure(
        url=TABULA_DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=SCHEMA,
        include_schemas=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(TABULA_DB_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        _create_schema(connection)
        connection.commit()
        connection = connection.execution_options(schema_translate_map={None: SCHEMA})
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=SCHEMA,
            include_schemas=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
