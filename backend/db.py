"""
Tabula — Layer di connessione DB (SQLite o PostgreSQL)
======================================================
Default: SQLite locale `./tabula.db` — zero dipendenze esterne.
Per PostgreSQL impostare TABULA_DB_URL con un URL postgresql+psycopg2://...

Con PostgreSQL lo schema `tabula` viene applicato a runtime via
schema_translate_map (i modelli non lo dichiarano).
Con SQLite lo schema non esiste: le tabelle vivono nel database direttamente.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TABULA_DB_URL = os.environ.get(
    "TABULA_DB_URL",
    "sqlite:///./tabula.db",
)

SCHEMA = "tabula"
IS_POSTGRES = TABULA_DB_URL.startswith("postgresql")
# Lo schema dedicato esiste solo su Postgres; su SQLite gli schemi non esistono,
# quindi SCHEMA è None (le tabelle vivono direttamente nel database).
if not IS_POSTGRES:
    SCHEMA = None

_connect_args = {} if IS_POSTGRES else {"check_same_thread": False}
_base_engine = create_engine(TABULA_DB_URL, pool_pre_ping=True, connect_args=_connect_args)

# schema_translate_map applicato solo con Postgres; SQLite non supporta schemi
engine = (
    _base_engine.execution_options(schema_translate_map={None: SCHEMA})
    if IS_POSTGRES
    else _base_engine
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
