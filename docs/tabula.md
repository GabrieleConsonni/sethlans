# Tabula — the visual component of Sethlans

**Tabula** is the board that makes visible what the subagents orchestrated by
[Sethlans](../README.md) are doing: it organizes work by **projects** (a Jira project or
an internal one) and, within each project, displays **epics**, **stories**, **tasks**, and the
state/consumption of the **agents** (a pool shared across projects).

It consists of a backend with a REST API (FastAPI + Postgres, `tabula` schema, Alembic
migrations) and a React frontend (Vite). Each epic/story/task has an associated
**Markdown** document (`md`); stories have a **phase** (`phase`). The active project
is selected from the combo box in the header (with the `+` to create a new one).

The subagents write to the backend via the API (see [tabula-protocol.md](../claude-config/tabula-protocol.md));
the frontend displays the state and updates automatically (polling ~4s). Updating the board
is **best-effort**: if it does not respond, development work continues anyway.

## Structure

```
backend/
├── tabula_server.py        # FastAPI API (CRUD endpoints + /state)
├── models.py               # SQLAlchemy ORM models (epics/stories/tasks/agents)
├── db.py                   # Postgres engine + `tabula` schema
├── alembic/                # migrations (env.py + versions/)
├── alembic.ini
├── seed.py                 # optional seed (canonical agents + demo)
└── requirements.txt
frontend/
├── index.html
├── package.json
├── vite.config.js
├── .env.example
└── src/
    ├── main.jsx
    ├── api.js              # API client
    ├── App.jsx             # state + routing between views
    ├── styles.css
    └── components/
        ├── ProjectSwitcher.jsx # project combo + create project (header)
        ├── Agenda.jsx      # home: epics (left) + stories (right)
        ├── StoryPage.jsx   # story detail: Munera + Periti tabs
        ├── Munera.jsx      # task board
        ├── Periti.jsx      # agent grid
        └── shared.jsx      # reused pieces (ColHeader, EditBox, etc.)
```

## Running with Docker (recommended)

You need [Docker Desktop](https://www.docker.com/products/docker-desktop/) running.

Double-click **`tabula.bat`** (or run `docker compose up --build -d` from a terminal).
The script builds the images, starts the containers, and opens the browser.

- Interface: <http://localhost:5173>
- API / docs: <http://localhost:9955/docs>

To stop everything: double-click **`stop-tabula.bat`** (or `docker compose down`).

The backend relies on an **external Postgres** (default: db `tabula`, schema `tabula`)
configured via `TABULA_DB_URL`. When the container starts, the migrations are applied
(`alembic upgrade head`). For local values (host/credentials) copy `.env.example` to
`.env` (gitignored); for a private npm registry see `docker-compose.override.yml.example`.

### Development mode (hot-reload)

Double-click **`dev-tabula.bat`** (or `docker compose -f docker-compose.dev.yml up --build`).

The `backend/` and `frontend/` sources are mounted into the containers: every change is
applied automatically, without rebuilding the images.

- Backend: `uvicorn --reload` reloads when Python files are saved.
- Frontend: Vite dev server with hot module replacement.

Same ports and same DB volume as normal mode. To stop: `stop-tabula.bat`.

## Quick start (without Docker)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Postgres: default postgresql+psycopg2://postgres:password@localhost:5432/tabula
# (override with the TABULA_DB_URL environment variable)
alembic upgrade head               # creates the `tabula` schema and the tables
python tabula_server.py            # http://localhost:9955  (docs: /docs)
```

The board starts **empty**. To populate canonical agents + demo data: `python seed.py`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env               # optional: change the backend URL
npm run dev                        # http://localhost:5173
```

The frontend reads `VITE_API_URL` (default `http://localhost:9955`). You can also change it at
runtime from the field at the top of the interface.

## API in brief

Resources: `projects`, `epics`, `stories`, `tasks`, `agents`. Each one with:

| Method | Path              | Action                    |
|--------|-------------------|---------------------------|
| GET    | `/{resource}`     | list (with filters)       |
| POST   | `/{resource}`     | create                    |
| GET    | `/{resource}/{id}`| read                      |
| PATCH  | `/{resource}/{id}`| partial update            |
| DELETE | `/{resource}/{id}`| delete                    |

Filters: `/epics?project_id=`, `/stories?epic_id=`, `/tasks?story_id=`, `/tasks?agent_id=`, `?status=`, `/projects?type=`.
Full snapshot: `GET /state`.

### Example: a subagent updates its own work

```bash
# takes a task
curl -X PATCH localhost:9955/tasks/t3 \
  -H "Content-Type: application/json" \
  -d '{"status":"progress","agent_id":"a2"}'

# updates the agent's state and consumption
curl -X PATCH localhost:9955/agents/a2 \
  -H "Content-Type: application/json" \
  -d '{"current_task":"Test end-to-end","status":"active","tokens":92000}'

# completes the task
curl -X PATCH localhost:9955/tasks/t3 -H "Content-Type: application/json" -d '{"status":"done"}'
```

## Data schema

```
Project { id, name, type, jira_key }                                   type: jira|internal ; jira_key: Jira key (empty if internal)
Epic   { id, title, desc, status, project_id, md, md_updated_at }       status: todo|progress|done
Story  { id, title, desc, status, phase, epic_id, md, md_updated_at }  status: todo|progress|done ; phase: analysis|ux|design|dev|done
Task   { id, title, status, story_id, agent_id, md, md_updated_at }    status: todo|progress|done
Agent  { id, name, current_task, status, tokens }                      status: active|idle (shared pool, not tied to a project)
```

Hierarchy: **Project → Epic → Story → Task**. Deleting a project cascade-removes the
linked epics/stories/tasks.

`md` = associated Markdown document (for stories it can contain HTML mockups in
` ```mockup ` blocks, rendered in the UI inside a sandboxed iframe).

## Notes

- CORS is open to all origins for development convenience: in production, restrict `allow_origins`.
- Persistence on Postgres (`tabula` schema), migrations with Alembic: `alembic upgrade head` / `alembic revision -m "..."`. Connection via `TABULA_DB_URL`.
- No authentication: add a token if exposed on the network.
