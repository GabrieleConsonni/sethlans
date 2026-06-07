# Tabula

Cruscotto per coordinare i subagenti di Claude: organizza il lavoro per **progetti** (un progetto Jira oppure uno interno) e, dentro ciascun progetto, visualizza **epiche**, **storie**, **task** e lo stato/consumo degli **agenti** (pool condiviso tra i progetti). Backend con API REST (FastAPI + Postgres, schema `tabula`, migrazioni Alembic) e frontend React (Vite). Ogni epica/storia/task ha un documento **Markdown** (`md`) associato; le storie hanno una **fase** (`phase`). Il progetto attivo si seleziona dalla combo nell'header (con il `+` per crearne uno nuovo).

I subagenti scrivono sul backend via API; il frontend mostra lo stato e si aggiorna in automatico (polling).

> **Orchestrazione** — il command `/sethlans` e i subagent che pilotano questo flusso
> stanno in [`claude-config/`](claude-config/README.md), con gli script per installarli
> nella home globale di Claude Code (`~/.claude/`).

## Struttura del repository

```
tabula/
├── README.md
├── backend/
│   ├── tabula_server.py        # API FastAPI (endpoint CRUD + /state)
│   ├── models.py               # modelli ORM SQLAlchemy (epics/stories/tasks/agents)
│   ├── db.py                   # engine Postgres + schema `tabula`
│   ├── alembic/                # migrazioni (env.py + versions/)
│   ├── alembic.ini
│   ├── seed.py                 # seed opzionale (agent canonici + demo)
│   ├── requirements.txt
│   └── .gitignore
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    ├── .env.example
    ├── .gitignore
    └── src/
        ├── main.jsx
        ├── api.js              # client delle API
        ├── App.jsx             # stato + routing tra le viste
        ├── styles.css
        └── components/
            ├── ProjectSwitcher.jsx # combo progetto + crea progetto (header)
            ├── Agenda.jsx      # home: epiche (sx) + storie (dx)
            ├── StoryPage.jsx   # dettaglio storia: tab Munera + Periti
            ├── Munera.jsx      # board dei task
            ├── Periti.jsx      # griglia agenti
            └── shared.jsx      # pezzi riusati (ColHeader, EditBox, ecc.)
```

## Avvio con Docker (consigliato)

Serve [Docker Desktop](https://www.docker.com/products/docker-desktop/) in esecuzione.

Doppio clic su **`tabula.bat`** (oppure da terminale `docker compose up --build -d`).
Lo script costruisce le immagini, avvia i container e apre il browser.

- Interfaccia: <http://localhost:5173>
- API / docs: <http://localhost:9955/docs>

Per fermare tutto: doppio clic su **`stop-tabula.bat`** (oppure `docker compose down`).

Il backend si appoggia a un **Postgres esterno** (default: `tabula` sull'host,
schema `tabula`) configurato via `TABULA_DB_URL`. All'avvio del container vengono
applicate le migrazioni (`alembic upgrade head`).

### Modalità sviluppo (hot-reload)

Doppio clic su **`dev-tabula.bat`** (oppure `docker compose -f docker-compose.dev.yml up --build`).

I sorgenti di `backend/` e `frontend/` sono montati nei container: ogni modifica
viene applicata automaticamente, senza ricostruire le immagini.

- Backend: `uvicorn --reload` ricarica al salvataggio dei file Python.
- Frontend: dev server di Vite con hot module replacement.

Stesse porte e stesso volume DB della modalità normale. Per fermare: `stop-tabula.bat`.

## Avvio rapido (senza Docker)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Postgres: default postgresql+psycopg2://postgres:password@localhost:5432/tabula
# (override con la variabile d'ambiente TABULA_DB_URL)
alembic upgrade head               # crea lo schema `tabula` e le tabelle
python tabula_server.py            # http://localhost:9955  (docs: /docs)
```

La board parte **vuota**. Per popolare agent canonici + dati demo: `python seed.py`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env               # opzionale: cambia l'URL del backend
npm run dev                        # http://localhost:5173
```

Il frontend legge `VITE_API_URL` (default `http://localhost:9955`). Puoi anche cambiarlo a runtime dal campo in alto nell'interfaccia.

## API in breve

Risorse: `projects`, `epics`, `stories`, `tasks`, `agents`. Ognuna con:

| Metodo | Path              | Azione                    |
|--------|-------------------|---------------------------|
| GET    | `/{risorsa}`      | lista (con filtri)        |
| POST   | `/{risorsa}`      | crea                      |
| GET    | `/{risorsa}/{id}` | leggi                     |
| PATCH  | `/{risorsa}/{id}` | modifica parziale         |
| DELETE | `/{risorsa}/{id}` | cancella                  |

Filtri: `/epics?project_id=`, `/stories?epic_id=`, `/tasks?story_id=`, `/tasks?agent_id=`, `?status=`, `/projects?type=`.
Snapshot completo: `GET /state`.

### Esempio: un subagente aggiorna il proprio lavoro

```bash
# prende in carico un task
curl -X PATCH localhost:9955/tasks/t3 \
  -H "Content-Type: application/json" \
  -d '{"status":"progress","agent_id":"a2"}'

# aggiorna stato e consumo dell'agente
curl -X PATCH localhost:9955/agents/a2 \
  -H "Content-Type: application/json" \
  -d '{"current_task":"Test end-to-end","status":"active","tokens":92000}'

# completa il task
curl -X PATCH localhost:9955/tasks/t3 -H "Content-Type: application/json" -d '{"status":"done"}'
```

## Schema dati

```
Project { id, name, type, jira_key }                                   type: jira|internal ; jira_key: chiave Jira (vuota se interno)
Epic   { id, title, desc, status, project_id, md, md_updated_at }       status: todo|progress|done
Story  { id, title, desc, status, phase, epic_id, md, md_updated_at }  status: todo|progress|done ; phase: analysis|ux|design|dev|done
Task   { id, title, status, story_id, agent_id, md, md_updated_at }    status: todo|progress|done
Agent  { id, name, current_task, status, tokens }                      status: active|idle (pool condiviso, non legato a un progetto)
```

Gerarchia: **Project → Epic → Story → Task**. Cancellando un progetto vengono rimosse a cascata epiche/storie/task collegati.

`md` = documento Markdown associato (per le storie può contenere mockup HTML in
blocchi ```mockup```, renderizzati nella UI in un iframe sandbox).

## Note

- CORS è aperto a tutte le origini per comodità di sviluppo: in produzione restringere `allow_origins`.
- Persistenza su Postgres (schema `tabula`), migrazioni con Alembic: `alembic upgrade head` / `alembic revision -m "..."`. Connessione via `TABULA_DB_URL`.
- Nessuna autenticazione: aggiungere un token se esposto in rete.
