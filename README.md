# Sethlans

**Sethlans** (the Etruscan god of fire and the forge) is a **subagent
orchestration** system for Claude Code: starting from a request (Jira key, Confluence link, or
free-form description) it coordinates the **PO → UX → architect → dev → review/test** workflow,
delegating each phase to a specialized subagent. Progress is made visible in real
time on **Tabula**, the board that serves as the system's visual component.

```
                          /sethlans  (orchestrator)
                               │
   product-owner → ux-designer → architect → dev (fe / be / fullstack) → reviewer / tester
                               │
                               ▼
                      Tabula  (board: epics · stories · tasks · agents)
```

## The components

| Component | What it is | Where |
|------------|-------|------|
| **`/sethlans`** | The orchestrator command: request ingest and phase coordination. | [`claude-config/commands/sethlans.md`](claude-config/commands/sethlans.md) |
| **Subagent** | 10 generic, reusable agents (PO, UX, architect, frontend, be-python, be-java, fullstack, devops, reviewer, tester). They make no assumptions about a project: they read the `CLAUDE.md` of the repo they work on. | [`claude-config/agents/`](claude-config/agents) |
| **Protocol** | The integration contract with the board (base URL, data model, enums, recipes): single source of truth cited by command and agents. | [`claude-config/tabula-protocol.md`](claude-config/tabula-protocol.md) |
| **Tabula** | The **visual component**: board (FastAPI + Postgres + React) that renders what the agents are doing. | [`docs/tabula.md`](docs/tabula.md) · `backend/` · `frontend/` |

Command, subagents, and protocol are **global** Claude Code configuration (they live in
`~/.claude/`); Tabula is a standalone **app** that the agents update via HTTP. Reflecting
state on the board is **best-effort and never blocking**: if Tabula does not respond, development
work proceeds all the same.

## The workflow in brief

1. **Healthcheck** of the Tabula board (best-effort).
2. **Product Owner** — ingest & analysis: find/create epic + story, set the `phase`.
3. **UX Designer** — HTML/CSS mockups, if the story requires UX workflows to validate.
4. **Architect** — architectural decisions + breakdown into tasks (with `agent_id` per type).
5. **DevOps** (on-demand) — prepares the ecosystem (updated repos, infra/services on Docker).
6. **Dev** — the target subagents implement the tasks (parallelizing the independent ones).
7. **Reviewer / Tester** — review of the diff and E2E/UI tests against the acceptance criteria.
8. **State cascade** and final summary.

The detail of each step is in [`claude-config/commands/sethlans.md`](claude-config/commands/sethlans.md).

## Getting started

### 1. Install the toolkit (command + subagent + protocol)

These files go in the global Claude Code home (`~/.claude/`). The scripts copy them:

```powershell
# Windows / PowerShell
cd claude-config; pwsh ./install.ps1          # -Force to overwrite
```
```bash
# macOS / Linux
cd claude-config && chmod +x install.sh && ./install.sh   # --force to overwrite
```

Restart Claude Code and use `/sethlans <Jira key | Confluence link | description>`.
Details: [`claude-config/README.md`](claude-config/README.md).

### 2. Start Tabula (the board)

```bash
docker compose up --build -d        # or: tabula.bat (Windows)
```
Interface → <http://localhost:5173> · API/docs → <http://localhost:9955/docs>.
Complete guide (Docker, running without Docker, API, data schema): [`docs/tabula.md`](docs/tabula.md).

### Prerequisites

- **Claude Code** with the toolkit installed.
- **Docker Desktop** + a reachable **Postgres** (for the board). Local values in `.env`
  (copy from `.env.example`); optional private npm registry via `docker-compose.override.yml`.
- For ingest from Jira/Confluence: the **Atlassian MCP** configured in Claude Code.
- On the project you work on, a **`CLAUDE.md`** describing stack/commands/environments (see
  [`CLAUDE.md`](CLAUDE.md) of this repo as an example).

## Repository structure

```
sethlans/
├── README.md                     # this file (Sethlans)
├── CLAUDE.md                     # project guide for the subagents
├── LICENSE · NOTICE              # Apache 2.0
├── claude-config/                # the Sethlans toolkit (global Claude Code config)
│   ├── commands/sethlans.md      #   the /sethlans command
│   ├── agents/                   #   the 10 generic subagents
│   ├── tabula-protocol.md        #   board API contract
│   └── install.ps1 / install.sh  #   installer → ~/.claude/
├── docs/
│   └── tabula.md                 # complete guide to the Tabula board
├── backend/                      # Tabula — FastAPI API + Postgres/Alembic
├── frontend/                     # Tabula — React/Vite SPA
└── docker-compose*.yml · *.bat   # starting the board
```

## License

Distributed under the **Apache 2.0** license — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
