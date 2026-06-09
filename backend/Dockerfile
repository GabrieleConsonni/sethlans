FROM python:3.12-slim

WORKDIR /app

# Dipendenze base (SQLite incluso in stdlib Python — nessuna dipendenza esterna).
# Per PostgreSQL usare requirements-postgres.txt passando --build-arg REQUIREMENTS=requirements-postgres.txt
ARG REQUIREMENTS=requirements.txt
COPY requirements.txt requirements-postgres.txt ./
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

COPY . .

# Default: SQLite locale su volume persistente.
# Per PostgreSQL: -e TABULA_DB_URL=postgresql+psycopg2://user:pass@host:5432/db
ENV TABULA_DB_URL=sqlite:////data/tabula.db

VOLUME ["/data"]

EXPOSE 9955

# Applica le migrazioni Alembic e poi avvia l'API.
CMD ["sh", "-c", "alembic upgrade head && python tabula_server.py"]
