# CLAUDE.md — Tabula

Guida per gli agenti che lavorano su questo repository. È il documento che i subagent
generici leggono per orientarsi: stack, comandi, struttura e convenzioni del progetto.

## Cos'è

**Tabula** è una board che visualizza il lavoro dei subagent di Claude, organizzato per
**progetti** → **epiche** → **storie** → **task**, più un pool condiviso di **agenti**.
Ogni epica/storia/task ha un documento **Markdown (`md`)**; le storie hanno una **`phase`**
che modella il flusso PO→UX→architect→dev. È composta da:

- **`backend/`** — API REST (FastAPI) su Postgres, schema dedicato `tabula`, migrazioni Alembic.
- **`frontend/`** — SPA React (Vite) che fa polling dello stato ogni ~4s.
- **`claude-config/`** — configurazione globale di Claude Code (command `/sethlans`, subagent,
  protocollo della board). Non fa parte dell'app: si installa in `~/.claude/` (vedi
  [`claude-config/README.md`](claude-config/README.md)).

## Stack

| Area      | Tecnologie |
|-----------|-----------|
| Backend   | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Uvicorn |
| Database  | PostgreSQL (schema `tabula` nel db `akn-dev-local`), psycopg2 |
| Frontend  | React 18, Vite 5, lucide-react (no framework UI aggiuntivi) |
| Runtime   | Docker / docker-compose (backend :9955, frontend :5173) |

## Struttura

```
backend/
  tabula_server.py     # API FastAPI: CRUD projects/epics/stories/tasks/agents + GET /state
  models.py            # ORM + enum applicativi (STATUS_*, PHASE_STORY, TYPE_PROJECT) + new_id()
  db.py                # engine Postgres + schema_translate_map({None: "tabula"})
  alembic/             # migrazioni (env.py + versions/)
  seed.py              # seed opzionale (agent canonici + dati demo)
  requirements.txt
frontend/
  src/api.js           # client delle API (legge VITE_API_URL)
  src/App.jsx          # stato globale + routing tra le viste
  src/components/      # Agenda, StoryPage, Munera (task), Periti (agenti), ProjectSwitcher, shared
claude-config/         # toolkit Sethlans (command + agent + protocollo) — vedi README dedicato
docker-compose.yml     # build+run (prod-like); docker-compose.dev.yml = hot-reload
```

## Come avviare

### Docker (consigliato)
Richiede Docker Desktop e un Postgres raggiungibile su `host.docker.internal:5432`.
```bash
docker compose up --build -d            # oppure: tabula.bat (Windows)
docker compose -f docker-compose.dev.yml up --build   # hot-reload di backend+frontend
docker compose down                     # stop  (oppure: stop-tabula.bat)
```
Interfaccia → http://localhost:5173 · API/docs → http://localhost:9955/docs

> Il build del frontend usa un secret `~/.npmrc` (registry/token Nexus) montato dal compose:
> serve un `.npmrc` valido nella home per `npm install` dietro il proxy aziendale.

### Senza Docker
```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate     # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head                                # crea schema `tabula` + tabelle
python tabula_server.py                             # :9955  (override porta: TABULA_PORT)
python seed.py                                       # opzionale: agent canonici + demo

# Frontend
cd frontend
npm install
copy .env.example .env                              # opzionale (VITE_API_URL)
npm run dev                                          # :5173
```

## Configurazione (variabili d'ambiente)

| Variabile        | Dove        | Default | Note |
|------------------|-------------|---------|------|
| `TABULA_DB_URL`  | backend     | `postgresql+psycopg2://postgres:password@localhost:5432/akn-dev-local` | connessione Postgres |
| `TABULA_PORT`    | backend     | `9955`  | porta API |
| `VITE_API_URL`   | frontend    | `http://localhost:9955` | base URL del backend (anche runtime, dal campo in header) |

## API & modello dati

Risorse REST uniformi (`GET/POST` collezione, `GET/PATCH/DELETE` per id):
`projects`, `epics`, `stories`, `tasks`, `agents`. Snapshot completo: `GET /state`.
Filtri: `/epics?project_id=`, `/stories?epic_id=`, `/tasks?story_id=`, `/tasks?agent_id=`, `?status=`.

```
Project { id, name, type, jira_key }                        type ∈ {jira, internal}
Epic    { id, title, desc, status, project_id, md }         status ∈ {todo, progress, done}
Story   { id, title, desc, status, phase, epic_id, md }     phase ∈ {analysis, ux, design, dev, done}
Task    { id, title, status, story_id, agent_id, md }       status ∈ {todo, progress, done}
Agent   { id, name, current_task, status, tokens }          status ∈ {active, idle}  (pool condiviso)
```
Gerarchia **Project → Epic → Story → Task** con delete a cascata. `md` = documento Markdown
(le storie possono contenere mockup HTML in blocchi ` ```mockup `, renderizzati in iframe sandbox).
`md_updated_at` lo imposta il server quando `md` cambia.

## Convenzioni (rispettarle)

- **ID generati dal server**: prefisso tipo + 8 hex (`new_id()` in `models.py`, es. `s1a2b3c4`).
  Mai inventarli lato client: usare l'`id` restituito dalle POST / letto dalle GET.
- **Enum validati nell'API**: usare solo i valori in `STATUS_WORK`/`STATUS_AGENT`/`PHASE_STORY`/
  `TYPE_PROJECT` (`models.py`). L'API rifiuta valori fuori enum.
- **Schema implicito**: i modelli NON dichiarano lo schema `tabula`; è tradotto a runtime via
  `schema_translate_map` (`db.py` e `alembic/env.py`). Non aggiungere `__table_args__={"schema": ...}`.
- **Migrazioni**: ogni cambio ai modelli richiede una revision Alembic
  (`alembic revision --autogenerate -m "..."` → revisione → `alembic upgrade head`).
  Non modificare lo schema a mano nel DB.
- **Backend in italiano**: docstring e commenti del progetto sono in italiano; mantenere lo stile.
- **CORS aperto** a tutte le origini per comodità di sviluppo (`tabula_server.py`): in produzione
  va ristretto. Nessuna autenticazione: non esporre in rete senza aggiungere un token.

## Test

Non è ancora configurata una suite automatica (niente `pytest`/test nel repo). Convenzione attesa
per nuovo codice: **pytest** lato backend (in `backend/tests/`, con DB di test o Testcontainers) e
verifica manuale del flusso UI lato frontend. Aggiungere `pytest` a `requirements.txt` quando si
introducono i primi test.

## Orchestrazione (Sethlans)

Il flusso PO→UX→architect→dev su questa board è guidato dal command `/sethlans` e dai subagent in
[`claude-config/`](claude-config/README.md). Il contratto d'integrazione con la board (base URL,
ricette, enum, mappa task→agent) è in [`claude-config/tabula-protocol.md`](claude-config/tabula-protocol.md):
è la **single source of truth** per le chiamate alla board. Aggiornare Tabula è **best-effort e mai
bloccante** — se la board non risponde, il lavoro di sviluppo prosegue comunque.
