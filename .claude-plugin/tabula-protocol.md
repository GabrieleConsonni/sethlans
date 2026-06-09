# Tabula Protocol — reflecting work state

`tabula` is the board that visually renders what the workspace subagents are doing.
It is a **FastAPI REST API + SQLite (default) or PostgreSQL** (configurable via `TABULA_DB_URL`,
managed with Alembic); the React frontend polls every 4s. Agents reflect their own state via the
**`tabula` MCP server** (preferred) or directly **via HTTP** (no files to write). Each epic/story/task
has a **Markdown document `md`** persisted in the DB.

This document is the **single source of truth** of the integration: the subagents and
the orchestration command reference it instead of duplicating the recipes.
It is **cross-project**: it lives in the global home (`~/.claude/`) and does not depend
on any specific workspace.

## Guiding principle — best-effort, never blocking
Updating Tabula is **observability**, not part of the real work.
- If Tabula does not respond (connection refused, timeout, HTTP error), **DO NOT block** the task: proceed with the real work and report in the result that the board update failed.
- Always wrap the calls in `try/catch` (PowerShell) and must not fail the turn over a network error toward the board.

## Preferred path — the `tabula` MCP server
The plugin ships a **stdio MCP server** (`tabula`) that wraps this REST API with typed,
enum-validated tools. **Prefer the MCP tools** over the raw HTTP/PowerShell recipes: they
are **cross-platform** (no shell dependency), encapsulate the find-or-create logic, and
validate enums at the schema. The PowerShell recipes below remain a **fallback** when the
MCP server is unavailable. Same best-effort rule: the tools return a soft error (never throw)
if the board is unreachable — keep working on the real task.

Configuration: the server reads `TABULA_API_URL` (default `http://localhost:9955`).

| MCP tool | What it does |
|---|---|
| `tabula_get_state` | Snapshot (healthcheck + read). Compact summary by default; `full=true` for the raw `/state`. |
| `tabula_upsert_project` | Find-or-create a project by name; patches `type/jira_key/md`. |
| `tabula_upsert_epic` | Find-or-create an epic by title in a project (`project_id` or `project_name`, the latter created if missing). |
| `tabula_upsert_story` | Find-or-create a story by title under an epic; sets `status/phase/md`. |
| `tabula_create_task` | Create a task under a story; assign by `agent_name` (find-or-register) or `agent_id`. |
| `tabula_set_status` | Set `status` of an epic/story/task (and `phase` for stories). |
| `tabula_get_or_register_agent` | Find-or-register an agent by name; optionally patch `status/current_task/tokens`. |
| `tabula_add_agent_tokens` | Increment an agent's cumulative `tokens` (read-modify-write). |
| `tabula_append_md` | Append text to the `md` of any entity (read-modify-write). |
| `tabula_request` | Low-level escape hatch: arbitrary REST call (only for cases not covered above). |

Typical flow with the tools: `tabula_upsert_project` → `tabula_upsert_epic` → `tabula_upsert_story`
→ `tabula_create_task` (dev) → `tabula_set_status`/`tabula_append_md` during work →
`tabula_get_or_register_agent` for the agent lifecycle.

## Base URL (raw HTTP / fallback)
- Default: `http://localhost:9955`. Override with the environment variable `TABULA_API_URL`.
- Healthcheck: `GET /state` (if it responds 200, the board is reachable).

## Data model (exact fields)
- **epic**: `id, title, desc, status, md, md_updated_at` — status ∈ `{todo, progress, done}`
- **story**: `id, title, desc, status, phase, epic_id, md, md_updated_at` — status ∈ `{todo, progress, done}`, phase ∈ `{analysis, ux, design, dev, done}`
- **task**: `id, title, status, story_id, agent_id?, md, md_updated_at` — status ∈ `{todo, progress, done}`
- **agent**: `id, name, current_task, status, tokens` — status ∈ `{active, idle}`

`md` is the associated Markdown document (analysis/mockups for stories, description +
architectural choices + work notes for tasks). `md_updated_at` is set by the
server when the `md` changes. IDs are server-generated (prefix `e/s/t/a` +
8 hex): **do not invent them**, always use the `id` returned by the POSTs or read from the GETs.

## Story phases (`phase`)
They model the PO→UX→architect→dev flow without touching the raw `status`:
- `analysis` — Product Owner: analysis in progress/to be done.
- `ux` — user-flow mockups are needed → UX Designer.
- `design` — ready for the architect (architectural decisions + breakdown into tasks).
- `dev` — tasks created and being worked on by the devs.
- `done` — story completed.
Typical transitions: `analysis → (ux) → design → dev → done`.

## Canonical agent names (Tabula records)
One `agent` record for each subagent, identified **by name** (the id is dynamic):

| subagent | `name` Tabula |
|---|---|
| product-owner | `product-owner` |
| ux-designer | `ux-designer` |
| architect | `architect` |
| frontend | `frontend` |
| be-python | `be-python` |
| be-java | `be-java` |
| fullstack | `fullstack` |
| reviewer | `reviewer` |
| tester | `tester` |
| devops | `devops` |

## Task-type → agent map
- UI / Angular → `frontend`
- BE Python (FastAPI/Polars) → `be-python`
- BE Java (Spring Boot) → `be-java`
- cross-repo / end-to-end slice → `fullstack`
- code review → `reviewer`
- test / QA / E2E → `tester`
- environment preparation / repo update / Docker stack startup-restart → `devops`
- `product-owner`, `ux-designer` and `architect` work on the story phases
  (analysis/ux/design), normally **without implementation tasks**: the PO creates/updates
  epics and stories, UX produces mockups in the md, the architect creates the tasks for the devs.

## Recipes (PowerShell — Windows environment)
The server runs on Windows; `Invoke-RestMethod` does native JSON parsing (no `jq`).

```powershell
$base = if ($env:TABULA_API_URL) { $env:TABULA_API_URL } else { 'http://localhost:9955' }
function Tab($method, $path, $bodyObj=$null) {
  $args = @{ Method = $method; Uri = "$base$path"; ContentType = 'application/json' }
  if ($bodyObj) { $args.Body = ($bodyObj | ConvertTo-Json -Depth 6) }
  Invoke-RestMethod @args
}

# Find-or-register an agent by name → returns the id
function Get-AgentId($name) {
  $a = (Tab GET '/agents') | Where-Object { $_.name -eq $name } | Select-Object -First 1
  if (-not $a) { $a = Tab POST '/agents' @{ name = $name; status = 'idle'; current_task = 'Inattivo'; tokens = 0 } }
  return $a.id
}
```

### Life cycle of a dev/reviewer/tester agent
```powershell
$me = Get-AgentId 'frontend'                                  # your canonical name
# start
Tab PATCH "/agents/$me" @{ status = 'active'; current_task = 'Form di login (s12)' }
Tab PATCH "/tasks/$taskId" @{ status = 'progress'; agent_id = $me }
# ... real work ...
# successful end
Tab PATCH "/tasks/$taskId" @{ status = 'done' }
Tab PATCH "/agents/$me" @{ status = 'idle'; current_task = 'Inattivo' }
```
On error/block: **leave the task in `progress`** (do not set it to `done`),
report the reason, and return the agent to `idle` only if you have really stopped working on it.

### Find-or-create epic (match by title, no server-side search exists)
```powershell
$epicTitle = 'NAU-177 Sistema di autenticazione'
$epic = (Tab GET '/epics') | Where-Object { $_.title -eq $epicTitle } | Select-Object -First 1
if (-not $epic) { $epic = Tab POST '/epics' @{ title = $epicTitle; desc = '...'; status = 'progress' } }
$epicId = $epic.id
```

### Find-or-create story under the epic (with phase and md) — done by the Product Owner
```powershell
$storyTitle = 'Login page'
$story = (Tab GET "/stories?epic_id=$epicId") | Where-Object { $_.title -eq $storyTitle } | Select-Object -First 1
if (-not $story) {
  $story = Tab POST '/stories' @{ title = $storyTitle; desc = '...'; status = 'todo'; phase = 'analysis'; epic_id = $epicId; md = '# Analysis...' }
}
$storyId = $story.id
# update analysis and phase:
Tab PATCH "/stories/$storyId" @{ md = '# Updated analysis...'; phase = 'design' }
```

### Create an assigned task with md (description + architectural choices) — done by the architect
```powershell
$agentId = Get-AgentId 'be-python'        # task-type → agent map
Tab POST '/tasks' @{ title = 'Endpoint POST /datasets'; status = 'todo'; story_id = $storyId; agent_id = $agentId; md = "## Work\n...\n## Architectural choices\n..." }
# the architect moves the story to the dev phase:
Tab PATCH "/stories/$storyId" @{ phase = 'dev'; status = 'progress' }
```

### Update the md (any entity)
```powershell
# read the current md and append (the devs at the end of work):
$t = Tab GET "/tasks/$taskId"
$new = $t.md + "`n`n## Work done`n- file X, choice Y, note Z"
Tab PATCH "/tasks/$taskId" @{ md = $new }   # md_updated_at is set by the server
```

### State cascade (orchestrator, optional)
- When the architect creates the tasks: move the story to `phase=dev`, `status=progress`.
- When **all** the tasks of a story are `done`: move the story to `status=done` and `phase=done`.
- When **all** the stories of an epic are `done`: move the epic to `done`.
```powershell
$tasks = Tab GET "/tasks?story_id=$storyId"
if ($tasks.Count -gt 0 -and ($tasks | Where-Object { $_.status -ne 'done' }).Count -eq 0) {
  Tab PATCH "/stories/$storyId" @{ status = 'done'; phase = 'done' }
}
```

## Operational notes
- To **release** a task from an agent: the PATCH ignores `null` fields, so you cannot clear `agent_id` via PATCH — reassign it to another agent or leave it unchanged.
- `tokens`: it is populated by **the orchestrator** (not the subagents, which do not know their own consumption) with a **cumulative estimate** at the close of each subagent — `GET` the current value, add the estimate, `PATCH`. It is best-effort and approximate; if the board does not respond, leave it unchanged.
- States: use **exactly** the enum values above, otherwise the server responds 422.
- Run the state PATCHes at the start and end of the work, not at every micro-step (avoid noise on the board).
