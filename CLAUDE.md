# CLAUDE.md — Tabula

Guide for agents working on this repository. It is the document that generic subagents
read to get oriented: the project's stack, commands, structure, and conventions.

## What it is

**Tabula** is a board that visualizes the work of Claude's subagents, organized by
**projects** → **epics** → **stories** → **tasks**, plus a shared pool of **agents**.
Every epic/story/task has a **Markdown (`md`)** document; stories have a **`phase`**
that models the PO→UX→architect→dev flow. It is composed of:

- **`backend/`** — REST API (FastAPI) on Postgres, dedicated `tabula` schema, Alembic migrations.
- **`frontend/`** — React SPA (Vite) that polls the state every ~4s.
- **`claude-config/`** — global Claude Code configuration (`/sethlans` command, subagents,
  board protocol). It is not part of the app: it is installed in `~/.claude/` (see
  [`claude-config/README.md`](claude-config/README.md)).

## Stack

| Area      | Technologies |
|-----------|-----------|
| Backend   | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Uvicorn |
| Database  | PostgreSQL (dedicated `tabula` schema), psycopg2 |
| Frontend  | React 18, Vite 5, lucide-react (no additional UI frameworks) |
| Runtime   | Docker / docker-compose (backend :9955, frontend :5173) |

## Structure

```
backend/
  tabula_server.py     # FastAPI API: CRUD projects/epics/stories/tasks/agents + GET /state
  models.py            # ORM + application enums (STATUS_*, PHASE_STORY, TYPE_PROJECT) + new_id()
  db.py                # Postgres engine + schema_translate_map({None: "tabula"})
  alembic/             # migrations (env.py + versions/)
  seed.py              # optional seed (canonical agents + demo data)
  requirements.txt
frontend/
  src/api.js           # API client (reads VITE_API_URL)
  src/App.jsx          # global state + routing between views
  src/components/      # Agenda, StoryPage, Munera (task), Periti (agents), ProjectSwitcher, shared
claude-config/         # Sethlans toolkit (command + agents + protocol) — see dedicated README
docker-compose.yml     # build+run (prod-like); docker-compose.dev.yml = hot-reload
```

## How to start

### Docker (recommended)
Requires Docker Desktop and a Postgres reachable at `host.docker.internal:5432`.
```bash
docker compose up --build -d            # or: tabula.bat (Windows)
docker compose -f docker-compose.dev.yml up --build   # hot-reload of backend+frontend
docker compose down                     # stop  (or: stop-tabula.bat)
```
Interface → http://localhost:5173 · API/docs → http://localhost:9955/docs

> The frontend build uses the public npm registry. Behind a private registry/proxy,
> provide a `~/.npmrc` as a secret via `docker-compose.override.yml` (see
> `docker-compose.override.yml.example`); the secret is optional and does not end up in the image.

### Without Docker
```bash
# Backend
cd backend
python -m venv .venv && .venv\Scripts\activate     # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head                                # creates `tabula` schema + tables
python tabula_server.py                             # :9955  (port override: TABULA_PORT)
python seed.py                                       # optional: canonical agents + demo

# Frontend
cd frontend
npm install
copy .env.example .env                              # optional (VITE_API_URL)
npm run dev                                          # :5173
```

## Configuration (environment variables)

| Variable         | Where       | Default | Notes |
|------------------|-------------|---------|------|
| `TABULA_DB_URL`  | backend     | `postgresql+psycopg2://postgres:password@localhost:5432/tabula` | Postgres connection |
| `TABULA_PORT`    | backend     | `9955`  | API port |
| `VITE_API_URL`   | frontend    | `http://localhost:9955` | backend base URL (also at runtime, from the header field) |

## API & data model

Uniform REST resources (`GET/POST` collection, `GET/PATCH/DELETE` by id):
`projects`, `epics`, `stories`, `tasks`, `agents`. Full snapshot: `GET /state`.
Filters: `/epics?project_id=`, `/stories?epic_id=`, `/tasks?story_id=`, `/tasks?agent_id=`, `?status=`.

```
Project { id, name, type, jira_key }                        type ∈ {jira, internal}
Epic    { id, title, desc, status, project_id, md }         status ∈ {todo, progress, done}
Story   { id, title, desc, status, phase, epic_id, md }     phase ∈ {analysis, ux, design, dev, done}
Task    { id, title, status, story_id, agent_id, md }       status ∈ {todo, progress, done}
Agent   { id, name, current_task, status, tokens }          status ∈ {active, idle}  (shared pool)
```
**Project → Epic → Story → Task** hierarchy with cascade delete. `md` = Markdown document
(stories can contain HTML mockups in ` ```mockup ` blocks, rendered in a sandboxed iframe).
`md_updated_at` is set by the server when `md` changes.

## Conventions (follow them)

- **Server-generated IDs**: type prefix + 8 hex (`new_id()` in `models.py`, e.g. `s1a2b3c4`).
  Never invent them on the client side: use the `id` returned by POSTs / read from GETs.
- **Enums validated in the API**: use only the values in `STATUS_WORK`/`STATUS_AGENT`/`PHASE_STORY`/
  `TYPE_PROJECT` (`models.py`). The API rejects values outside the enum.
- **Implicit schema**: the models do NOT declare the `tabula` schema; it is translated at runtime via
  `schema_translate_map` (`db.py` and `alembic/env.py`). Do not add `__table_args__={"schema": ...}`.
- **Migrations**: every change to the models requires an Alembic revision
  (`alembic revision --autogenerate -m "..."` → review → `alembic upgrade head`).
  Do not modify the schema by hand in the DB.
- **Code in Italian**: docstrings and comments in this repo are currently written in Italian
  (the prose docs are in English); keep the existing style when editing code.
- **Open CORS** to all origins for development convenience (`tabula_server.py`): in production
  it must be restricted. No authentication: do not expose on the network without adding a token.

## Tests

An automated suite is not yet configured (no `pytest`/tests in the repo). Expected convention
for new code: **pytest** on the backend (in `backend/tests/`, with a test DB or Testcontainers) and
manual verification of the UI flow on the frontend. Add `pytest` to `requirements.txt` when the
first tests are introduced.

## Orchestration (Sethlans)

The PO→UX→architect→dev flow on this board is driven by the `/sethlans` command and the subagents in
[`claude-config/`](claude-config/README.md). The integration contract with the board (base URL,
recipes, enums, task→agent map) is in [`claude-config/tabula-protocol.md`](claude-config/tabula-protocol.md):
it is the **single source of truth** for calls to the board. Updating Tabula is **best-effort and never
blocking** — if the board does not respond, development work continues anyway.
