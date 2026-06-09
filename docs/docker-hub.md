# Tabula — Docker Hub & distribuzione

Tabula è distribuita come due immagini pre-buildiate su Docker Hub:

- [`gifsonick/tabula-backend`](https://hub.docker.com/r/gifsonick/tabula-backend)
- [`gifsonick/tabula-frontend`](https://hub.docker.com/r/gifsonick/tabula-frontend)

Gli utenti finali non devono clonare il repository né installare dipendenze — basta Docker.

---

## Avvio rapido (utente finale)

```bash
curl -O https://raw.githubusercontent.com/GabrieleConsonni/sethlans/main/docker-compose.dist.yml
docker compose -f docker-compose.dist.yml up -d
```

- Interfaccia → http://localhost:5173
- API / docs → http://localhost:9955/docs

Il database è **SQLite** (default), persistito in un volume Docker named `tabula-data`. Zero dipendenze esterne.

### Con PostgreSQL

```bash
TABULA_DB_URL=postgresql+psycopg2://user:pass@host:5432/tabula \
docker compose -f docker-compose.dist.yml up -d
```

---

## Tag disponibili

| Tag | Quando viene aggiornato |
|---|---|
| `latest` | Ogni push su `main` |
| `1.2.3` | Al tag git `v1.2.3` |
| `1.2` | Al tag git `v1.2.x` |
| `sha-abc1234` | Ogni build (SHA breve del commit) |

---

## Pubblicazione automatica (maintainer)

Le immagini vengono buildiate e pushate su Docker Hub via **GitHub Actions**
(`.github/workflows/docker-publish.yml`) in modo automatico.

### Prerequisiti (da fare una volta sola)

1. Crea un account su [hub.docker.com](https://hub.docker.com)
2. Vai su **Account Settings → Security → New Access Token**
   - Nome: `github-actions`, permessi: `Read & Write`
   - Copia il token (visibile solo una volta)
3. Nel repo GitHub → **Settings → Secrets and variables → Actions**:
   - `DOCKER_USERNAME` = il tuo username Docker Hub
   - `DOCKER_TOKEN` = il token appena creato

### Rilasciare una versione

```bash
git tag v1.0.0
git push origin v1.0.0
```

GitHub Actions builda e pusha automaticamente con i tag `latest`, `1.0.0`, `1.0` e `sha-*`.

### Build manuale (opzionale)

```bash
# Backend
docker build -t gifsonick/tabula-backend:latest ./backend
docker push gifsonick/tabula-backend:latest

# Frontend
docker build -t gifsonick/tabula-frontend:latest ./frontend
docker push gifsonick/tabula-frontend:latest
```

---

## Build con PostgreSQL

Per produrre un'immagine backend con il driver PostgreSQL incluso:

```bash
docker build \
  --build-arg REQUIREMENTS=requirements-postgres.txt \
  -t gifsonick/tabula-backend:postgres \
  ./backend
```
