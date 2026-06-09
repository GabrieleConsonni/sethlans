FROM python:3.12-slim

WORKDIR /app

# Dipendenze uguali a prescindere dal database: includono sempre psycopg2,
# così l'immagine funziona sia con SQLite (default) sia con PostgreSQL.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: SQLite locale su volume persistente.
# Per PostgreSQL: -e TABULA_DB_URL=postgresql+psycopg2://user:pass@host:5432/db
ENV TABULA_DB_URL=sqlite:////data/tabula.db

VOLUME ["/data"]

EXPOSE 9955

# Applica le migrazioni Alembic e poi avvia l'API.
CMD ["sh", "-c", "alembic upgrade head && python tabula_server.py"]
