# Sethlans

**Sethlans** (il dio etrusco del fuoco e della forgia) è un sistema di **orchestrazione di
subagent** per Claude Code: a partire da una richiesta (chiave Jira, link Confluence o
descrizione libera) coordina il flusso **PO → UX → architect → dev → review/test**,
delegando ogni fase a un subagent specializzato. L'avanzamento è reso visibile in tempo
reale su **Tabula**, la board che fa da componente visivo del sistema.

```
                          /sethlans  (orchestratore)
                               │
   product-owner → ux-designer → architect → dev (fe / be / fullstack) → reviewer / tester
                               │
                               ▼
                      Tabula  (board: epiche · storie · task · agenti)
```

## I componenti

| Componente | Cos'è | Dove |
|------------|-------|------|
| **`/sethlans`** | Il command orchestratore: ingest della richiesta e coordinamento delle fasi. | [`claude-config/commands/sethlans.md`](claude-config/commands/sethlans.md) |
| **Subagent** | 10 agent generici e riusabili (PO, UX, architect, frontend, be-python, be-java, fullstack, devops, reviewer, tester). Non assumono un progetto: leggono il `CLAUDE.md` del repo su cui lavorano. | [`claude-config/agents/`](claude-config/agents) |
| **Protocollo** | Il contratto d'integrazione con la board (base URL, modello dati, enum, ricette): single source of truth citata da command e agent. | [`claude-config/tabula-protocol.md`](claude-config/tabula-protocol.md) |
| **Tabula** | Il **componente visivo**: board (FastAPI + Postgres + React) che renderizza cosa fanno gli agent. | [`docs/tabula.md`](docs/tabula.md) · `backend/` · `frontend/` |

Command, subagent e protocollo sono configurazione **globale** di Claude Code (vivono in
`~/.claude/`); Tabula è un'**app** a sé che gli agent aggiornano via HTTP. Riflettere lo
stato sulla board è **best-effort e mai bloccante**: se Tabula non risponde, il lavoro
di sviluppo prosegue lo stesso.

## Il flusso in breve

1. **Healthcheck** della board Tabula (best-effort).
2. **Product Owner** — ingest & analisi: trova/crea epica + storia, imposta la `phase`.
3. **UX Designer** — mockup HTML/CSS, se la storia richiede flussi UX da validare.
4. **Architect** — scelte architetturali + scomposizione in task (con `agent_id` per tipo).
5. **DevOps** (on-demand) — prepara l'ecosistema (repo aggiornati, infra/servizi su Docker).
6. **Dev** — i subagent target implementano i task (parallelizzando gli indipendenti).
7. **Reviewer / Tester** — review del diff e test E2E/UI sui criteri di accettazione.
8. **Cascata di stato** e riepilogo finale.

Il dettaglio di ogni passo è in [`claude-config/commands/sethlans.md`](claude-config/commands/sethlans.md).

## Come iniziare

### 1. Installa il toolkit (command + subagent + protocollo)

Questi file vanno nella home globale di Claude Code (`~/.claude/`). Gli script li copiano:

```powershell
# Windows / PowerShell
cd claude-config; pwsh ./install.ps1          # -Force per sovrascrivere
```
```bash
# macOS / Linux
cd claude-config && chmod +x install.sh && ./install.sh   # --force per sovrascrivere
```

Riavvia Claude Code e usa `/sethlans <chiave Jira | link Confluence | descrizione>`.
Dettagli: [`claude-config/README.md`](claude-config/README.md).

### 2. Avvia Tabula (la board)

```bash
docker compose up --build -d        # oppure: tabula.bat (Windows)
```
Interfaccia → <http://localhost:5173> · API/docs → <http://localhost:9955/docs>.
Guida completa (Docker, avvio senza Docker, API, schema dati): [`docs/tabula.md`](docs/tabula.md).

### Prerequisiti

- **Claude Code** con il toolkit installato.
- **Docker Desktop** + un **Postgres** raggiungibile (per la board). Valori locali in `.env`
  (copia da `.env.example`); registry npm privato opzionale via `docker-compose.override.yml`.
- Per l'ingest da Jira/Confluence: l'**MCP Atlassian** configurato in Claude Code.
- Sul progetto su cui lavori, un **`CLAUDE.md`** che descriva stack/comandi/ambienti (vedi
  [`CLAUDE.md`](CLAUDE.md) di questo repo come esempio).

## Struttura del repository

```
sethlans/
├── README.md                     # questo file (Sethlans)
├── CLAUDE.md                     # guida progetto per i subagent
├── LICENSE · NOTICE              # Apache 2.0
├── claude-config/                # il toolkit Sethlans (config globale di Claude Code)
│   ├── commands/sethlans.md      #   il command /sethlans
│   ├── agents/                   #   i 10 subagent generici
│   ├── tabula-protocol.md        #   contratto API della board
│   └── install.ps1 / install.sh  #   installer → ~/.claude/
├── docs/
│   └── tabula.md                 # guida completa della board Tabula
├── backend/                      # Tabula — API FastAPI + Postgres/Alembic
├── frontend/                     # Tabula — SPA React/Vite
└── docker-compose*.yml · *.bat   # avvio della board
```

## Licenza

Distribuito con licenza **Apache 2.0** — vedi [`LICENSE`](LICENSE) e [`NOTICE`](NOTICE).
