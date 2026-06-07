"""
Tabula — Layer di connessione DB (Postgres + SQLAlchemy)
========================================================
Tabula si appoggia a un Postgres esistente in uno schema dedicato `tabula`.
Lo schema è applicato a runtime con `schema_translate_map` (i modelli non lo
dichiarano), così la stessa metadata serve sia all'app sia ad Alembic.

Connessione configurabile via env `TABULA_DB_URL`
(default: il Postgres di dev `akn-dev-local`).
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SCHEMA = "tabula"

TABULA_DB_URL = os.environ.get(
    "TABULA_DB_URL",
    "postgresql+psycopg2://postgres:password@localhost:5432/akn-dev-local",
)

# `schema_translate_map={None: SCHEMA}` mappa le tabelle (schema implicito) sullo
# schema `tabula`. pool_pre_ping evita connessioni stale.
engine = create_engine(TABULA_DB_URL, pool_pre_ping=True).execution_options(
    schema_translate_map={None: SCHEMA}
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
