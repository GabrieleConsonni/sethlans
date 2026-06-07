# Sethlans toolkit — subagent orchestration on Tabula

This folder is the core of [Sethlans](../README.md): the **global** Claude Code
configuration that runs the PO→UX→architect→dev flow, visualized on the
[Tabula](../docs/tabula.md) board:

```
claude-config/
├── commands/
│   └── sethlans.md        # the /sethlans command (the orchestrator)
├── agents/                # the 10 generic subagents (reusable on any project)
│   ├── architect.md
│   ├── be-java.md
│   ├── be-python.md
│   ├── devops.md
│   ├── frontend.md
│   ├── fullstack.md
│   ├── product-owner.md
│   ├── reviewer.md
│   ├── tester.md
│   └── ux-designer.md
├── tabula-protocol.md     # the board's API contract (referenced by command + agents)
├── install.ps1            # Windows/PowerShell installer
└── install.sh             # macOS/Linux installer
```

## How it works

- **`/sethlans`** is the orchestrator: it ingests the request (Jira key, Confluence
  link, or free-form description), then coordinates the subagents phase by phase and
  reflects the state on the Tabula board via HTTP.
- The **subagents are generic**: they assume no specific project. They read the spec
  of the repo they work on from the current project's `CLAUDE.md`.
- **`tabula-protocol.md`** is the single source of truth for the integration with the
  board (base URL, data model, `status`/`phase` enums, PowerShell recipes). The command
  and agents reference it instead of duplicating the recipes.

## Installation

These files must live in Claude Code's global home (`~/.claude/`), not in the repo.
The scripts copy them to the right place.

**Windows / PowerShell**
```powershell
cd claude-config
pwsh ./install.ps1          # add -Force to overwrite
```

**macOS / Linux**
```bash
cd claude-config
chmod +x install.sh
./install.sh                # add --force to overwrite
```

After installation, **restart Claude Code** and type `/sethlans <request>`.

## Prerequisites for the full flow

- The **Tabula** board running (see [docs/tabula.md](../docs/tabula.md)).
  Default `http://localhost:9955`, override with the `TABULA_API_URL` environment variable.
- The project you work on should have a **`CLAUDE.md`** describing the stack, repos,
  commands, and environments: that is where the generic subagents orient themselves from.
- For ingest from Jira/Confluence you need the **Atlassian MCP** configured in Claude Code.

## A note on paths

`commands/sethlans.md` and `tabula-protocol.md` contain some environment references
(e.g. the local path of the Tabula backend and the `~/.claude/...` references). They are
meant for the original development machine: if your setup differs, adapt those references
after installation.
