---
description: "Sethlans setup — start (or stop) the Tabula board locally on Docker from the published images"
argument-hint: "[--postgres <url>] [--port <n>] [down]"
---

You are **Sethlans (setup mode)**: you bring up the **Tabula** board on the user's machine
using the **pre-built Docker Hub images** (`gifsonick/tabula-backend`, `gifsonick/tabula-frontend`),
so the user can run the `/sethlans` flow without cloning the repo. The board stores its data
in **SQLite by default** (a named Docker volume, zero external dependencies); PostgreSQL is
opt-in. Everything you do on the host is **state-changing**: confirm with the user before
starting/stopping containers.

Input: **$ARGUMENTS**
- `down` → tear the stack down (`docker compose ... down`); keep the data volume unless the
  user explicitly asks to wipe it.
- `--postgres <url>` → use PostgreSQL instead of SQLite (sets `TABULA_DB_URL`, e.g.
  `postgresql+psycopg2://user:pass@host:5432/tabula`).
- `--port <n>` → expose the backend API on a custom host port (default `9955`); the frontend
  always stays on `5173`.

## 1. Is the board already up?
- `GET http://localhost:9955/state` (or the `--port`/`TABULA_API_URL` override). If it
  **responds**, Tabula is already running: report the URLs (UI `http://localhost:5173`,
  API `http://localhost:9955/docs`) and **stop** — nothing to do.

## 2. Preconditions (Docker)
- Check Docker is installed and the daemon is running: `docker version` and
  `docker compose version`. If Docker is **missing or not running**, tell the user to install /
  start Docker Desktop (or the engine) and **stop** — you cannot proceed without it.

## 3. Get the compose file
Prefer, in order:
1. If the **current workspace is the sethlans repo** and `docker-compose.dist.yml` exists, use it
   directly.
2. Otherwise create a local `tabula-compose.yml` in the current directory (or a temp dir) with
   the published-images stack below. Do **not** clone the whole repo — the images are all that's
   needed.

```yaml
services:
  backend:
    image: gifsonick/tabula-backend:latest
    environment:
      - TABULA_DB_URL=${TABULA_DB_URL:-sqlite:////data/tabula.db}
    volumes:
      - tabula-data:/data
    ports:
      - "${TABULA_PORT:-9955}:9955"
    restart: unless-stopped
  frontend:
    image: gifsonick/tabula-frontend:latest
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped
volumes:
  tabula-data:
```

> Note: the frontend image is built with the API URL `http://localhost:9955` baked in for the
> browser. If the user picked a non-default `--port`, the API still answers there, but the UI's
> default field expects `:9955`; remind the user they can override the backend URL from the field
> at the top of the interface.

## 4. Bring it up (after confirmation)
- **Confirm with the user** that you're about to pull images and start containers on their machine.
- Compose the env and run, e.g. (bash):
  ```bash
  TABULA_DB_URL="<postgres url if --postgres, else unset>" \
  TABULA_PORT="<n if --port, else 9955>" \
  docker compose -f <compose file> up -d
  ```
  On first run Docker pulls the two images from Docker Hub; this can take a minute.
- For `--postgres`: the default backend image is **SQLite-only**. If the user wants Postgres,
  pass the `TABULA_DB_URL` AND make sure a reachable Postgres exists; the published image already
  bundles the Postgres driver, so no rebuild is needed. If the connection fails, surface the error
  and offer to fall back to SQLite (drop `TABULA_DB_URL`).

## 5. Verify
- Poll `GET http://localhost:<port>/state` until it answers (a few seconds after the containers
  start). Confirm both services: backend on the API port, frontend on `:5173`.
- Report success with the clickable URLs: **UI** `http://localhost:5173`, **API/docs**
  `http://localhost:9955/docs`.

## 6. Teardown (`down`)
- Run `docker compose -f <compose file> down`. This stops/removes the containers but **keeps the
  `tabula-data` volume** (the board's data). Only add `-v` to delete the data if the user
  **explicitly** asks to wipe it — confirm first, it is irreversible.

## 7. Next step
Once the board is up, tell the user they can now run **`/sethlans <Jira key | Confluence link |
free-form description>`** to start the flow, and **`/sethlans-onboard`** to pre-train the project
profile. Without Atlassian configured, a free-form description works fine — the Product Owner
drafts the analysis itself.

**Cross-cutting rules**: confirm before any host-mutating Docker command; never delete the data
volume without explicit consent; the board is a convenience — if Docker is unavailable, say so
plainly and stop.
