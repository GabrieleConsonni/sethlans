# Protocollo Tabula — riflessione dello stato di lavoro

`tabula` è la board che renderizza visivamente cosa stanno facendo i subagent del
workspace. Vive in `c:\sviluppo\labs\tabula` come **API REST FastAPI + Postgres**
(schema dedicato `tabula` nel db `akn-dev-local`, gestito con Alembic); il frontend
React fa polling ogni 4s. Gli agenti riflettono il proprio stato **solo via HTTP**
(nessun file da scrivere). Ogni epica/storia/task ha un **documento Markdown `md`**
persistito a DB.

Questo documento è la **single source of truth** dell'integrazione: i subagent e
il comando di orchestrazione lo referenziano invece di duplicare le ricette.
È **trasversale ai progetti**: vive nella home globale (`~/.claude/`) e non dipende
da alcun workspace specifico.

## Principio guida — best-effort, mai bloccante
Aggiornare Tabula è **osservabilità**, non parte del lavoro reale.
- Se Tabula non risponde (connection refused, timeout, errore HTTP), **NON bloccare** il task: procedi col lavoro vero e segnala nel risultato che l'aggiornamento board è fallito.
- Avvolgi sempre le chiamate in `try/catch` (PowerShell) e non far fallire il turno per un errore di rete verso la board.

## Base URL
- Default: `http://localhost:9955`. Override con la variabile d'ambiente `TABULA_API_URL`.
- Healthcheck: `GET /state` (se risponde 200, la board è raggiungibile).

## Modello dati (campi esatti)
- **epic**: `id, title, desc, status, md, md_updated_at` — status ∈ `{todo, progress, done}`
- **story**: `id, title, desc, status, phase, epic_id, md, md_updated_at` — status ∈ `{todo, progress, done}`, phase ∈ `{analysis, ux, design, dev, done}`
- **task**: `id, title, status, story_id, agent_id?, md, md_updated_at` — status ∈ `{todo, progress, done}`
- **agent**: `id, name, current_task, status, tokens` — status ∈ `{active, idle}`

`md` è il documento Markdown associato (analisi/mockup per le storie, descrizione +
scelte architetturali + note di lavoro per i task). `md_updated_at` è impostato dal
server quando l'`md` cambia. Gli ID sono generati dal server (prefisso `e/s/t/a` +
8 hex): **non inventarli**, usa sempre l'`id` restituito dalle POST o letto dalle GET.

## Fasi della storia (`phase`)
Modellano il flusso PO→UX→architect→dev senza toccare lo `status` grezzo:
- `analysis` — Product Owner: analisi in corso/da fare.
- `ux` — servono mockup di flussi utente → UX Designer.
- `design` — pronta per l'architect (decisioni architetturali + scomposizione in task).
- `dev` — task creati e in lavorazione dai dev.
- `done` — storia completata.
Transizioni tipiche: `analysis → (ux) → design → dev → done`.

## Nomi canonici degli agent (record Tabula)
Un record `agent` per ogni subagent, identificato **per nome** (l'id è dinamico):

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

## Mappa tipo-task → agent
- UI / Angular → `frontend`
- BE Python (FastAPI/Polars) → `be-python`
- BE Java (Spring Boot) → `be-java`
- cross-repo / slice end-to-end → `fullstack`
- code review → `reviewer`
- test / QA / E2E → `tester`
- preparazione ambiente / aggiornamento repo / avvio-riavvio stack Docker → `devops`
- `product-owner`, `ux-designer` e `architect` lavorano sulle fasi della storia
  (analysis/ux/design), di norma **senza task implementativi**: il PO crea/aggiorna
  epiche e storie, l'UX produce mockup nell'md, l'architect crea i task per i dev.

## Ricette (PowerShell — ambiente Windows)
Il server gira su Windows; `Invoke-RestMethod` fa il parsing JSON nativo (niente `jq`).

```powershell
$base = if ($env:TABULA_API_URL) { $env:TABULA_API_URL } else { 'http://localhost:9955' }
function Tab($method, $path, $bodyObj=$null) {
  $args = @{ Method = $method; Uri = "$base$path"; ContentType = 'application/json' }
  if ($bodyObj) { $args.Body = ($bodyObj | ConvertTo-Json -Depth 6) }
  Invoke-RestMethod @args
}

# Trova-o-registra un agent per nome → ritorna l'id
function Get-AgentId($name) {
  $a = (Tab GET '/agents') | Where-Object { $_.name -eq $name } | Select-Object -First 1
  if (-not $a) { $a = Tab POST '/agents' @{ name = $name; status = 'idle'; current_task = 'Inattivo'; tokens = 0 } }
  return $a.id
}
```

### Ciclo di vita di un agent dev/reviewer/tester
```powershell
$me = Get-AgentId 'frontend'                                  # il tuo nome canonico
# avvio
Tab PATCH "/agents/$me" @{ status = 'active'; current_task = 'Form di login (s12)' }
Tab PATCH "/tasks/$taskId" @{ status = 'progress'; agent_id = $me }
# ... lavoro reale ...
# fine OK
Tab PATCH "/tasks/$taskId" @{ status = 'done' }
Tab PATCH "/agents/$me" @{ status = 'idle'; current_task = 'Inattivo' }
```
In caso di errore/blocco: **lascia il task in `progress`** (non metterlo `done`),
riporta il motivo, e riporta l'agent a `idle` solo se hai davvero smesso di lavorarci.

### Trova-o-crea epica (match per titolo, non esiste ricerca server-side)
```powershell
$epicTitle = 'NAU-177 Sistema di autenticazione'
$epic = (Tab GET '/epics') | Where-Object { $_.title -eq $epicTitle } | Select-Object -First 1
if (-not $epic) { $epic = Tab POST '/epics' @{ title = $epicTitle; desc = '...'; status = 'progress' } }
$epicId = $epic.id
```

### Trova-o-crea storia sotto l'epica (con fase e md) — lo fa il Product Owner
```powershell
$storyTitle = 'Pagina di login'
$story = (Tab GET "/stories?epic_id=$epicId") | Where-Object { $_.title -eq $storyTitle } | Select-Object -First 1
if (-not $story) {
  $story = Tab POST '/stories' @{ title = $storyTitle; desc = '...'; status = 'todo'; phase = 'analysis'; epic_id = $epicId; md = '# Analisi...' }
}
$storyId = $story.id
# aggiornare analisi e fase:
Tab PATCH "/stories/$storyId" @{ md = '# Analisi aggiornata...'; phase = 'design' }
```

### Creare un task assegnato con md (descrizione + scelte architetturali) — lo fa l'architect
```powershell
$agentId = Get-AgentId 'be-python'        # mappa tipo-task → agent
Tab POST '/tasks' @{ title = 'Endpoint POST /datasets'; status = 'todo'; story_id = $storyId; agent_id = $agentId; md = "## Lavoro\n...\n## Scelte architetturali\n..." }
# l'architect porta la storia in fase dev:
Tab PATCH "/stories/$storyId" @{ phase = 'dev'; status = 'progress' }
```

### Aggiornare l'md (qualsiasi entità)
```powershell
# leggere l'md corrente e fare append (i dev a fine lavoro):
$t = Tab GET "/tasks/$taskId"
$nuovo = $t.md + "`n`n## Lavoro svolto`n- file X, scelta Y, nota Z"
Tab PATCH "/tasks/$taskId" @{ md = $nuovo }   # md_updated_at viene impostato dal server
```

### Cascata di stato (orchestratore, opzionale)
- Quando l'architect crea i task: porta la storia a `phase=dev`, `status=progress`.
- Quando **tutti** i task di una storia sono `done`: porta la storia a `status=done` e `phase=done`.
- Quando **tutte** le storie di un'epica sono `done`: porta l'epica a `done`.
```powershell
$tasks = Tab GET "/tasks?story_id=$storyId"
if ($tasks.Count -gt 0 -and ($tasks | Where-Object { $_.status -ne 'done' }).Count -eq 0) {
  Tab PATCH "/stories/$storyId" @{ status = 'done'; phase = 'done' }
}
```

## Note operative
- Per **rilasciare** un task da un agent: il PATCH ignora i campi `null`, quindi non puoi azzerare `agent_id` via PATCH — riassegnalo a un altro agent o lascialo invariato.
- `tokens`: lo popola **l'orchestratore** (non i subagent, che non conoscono il proprio consumo) con una **stima cumulativa** alla chiusura di ogni subagent — `GET` valore corrente, somma la stima, `PATCH`. È best-effort e approssimativo; se la board non risponde, lascialo invariato.
- Stati: usa **esattamente** i valori enum sopra, altrimenti il server risponde 422.
- Esegui le PATCH di stato all'inizio e alla fine del lavoro, non a ogni micro-step (evita rumore sulla board).
