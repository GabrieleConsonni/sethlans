FROM python:3.12-slim

WORKDIR /app

# Dipendenze installate per prime per sfruttare la cache dei layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistenza su Postgres esterno: configurare TABULA_DB_URL.
# Default: Postgres in esecuzione sull'host (vedi docker-compose: host.docker.internal).
ENV TABULA_DB_URL=postgresql+psycopg2://postgres:password@host.docker.internal:5432/tabula

EXPOSE 9955

# Applica le migrazioni Alembic (crea lo schema `tabula`) e poi avvia l'API.
CMD ["sh", "-c", "alembic upgrade head && python tabula_server.py"]
