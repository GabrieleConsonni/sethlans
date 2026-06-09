# Sethlans toolkit — subagent orchestration on Tabula

This folder contains the **installer scripts** for the Sethlans toolkit.
The source of truth for the command, subagents, and protocol has moved to
[`../.claude-plugin/`](../.claude-plugin/), which is also the Claude Code
plugin bundle.

```
.claude-plugin/          ← source of truth (plugin bundle)
  plugin.json            # manifest
  skills/
    sethlans.md          # the /sethlans orchestrator skill
    sethlans-onboard.md  # /sethlans-onboard: pre-train the project profile on Tabula
    sethlans-setup.md    # /sethlans-setup: start the Tabula board on Docker
  agents/                # the 10 generic subagents (reusable on any project)
    architect.md
    be-java.md
    be-python.md
    devops.md
    frontend.md
    fullstack.md
    product-owner.md
    reviewer.md
    tester.md
    ux-designer.md
  tabula-protocol.md     # the board's API contract (referenced by skill + agents)

claude-config/           ← this folder (installers only)
  install.ps1            # Windows/PowerShell manual installer
  install.sh             # macOS/Linux manual installer
  README.md
```

## How it works

- **`/sethlans`** is the orchestrator: it ingests the request (Jira key, Confluence
  link, or free-form description), then coordinates the subagents phase by phase and
  reflects the state on the Tabula board via HTTP.
- The **subagents are generic**: they assume no specific project. They read the spec
  of the repo they work on from the current project's `CLAUDE.md`.
- **`tabula-protocol.md`** is the single source of truth for the integration with the
  board (base URL, data model, `status`/`phase` enums, PowerShell recipes).

## Installation

### Option A — Claude Code plugin (recommended)

```bash
/plugin marketplace add anthropics/claude-plugins-community
/plugin install sethlans@claude-community
```

### Option B — Manual install (legacy)

These scripts copy the files from `.claude-plugin/` to `~/.claude/`.

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

## Source of truth & keeping in sync

`.claude-plugin/` is the **source of truth** for the command, subagents, and protocol.

- **To change** the skill/agents/protocol: edit them under `.claude-plugin/`, commit,
  then either submit to the plugin marketplace or re-run the installer with `-Force`/`--force`.
- Do **not** hand-edit files in `~/.claude/` — those edits would be overwritten on the
  next install and are not tracked.

## Prerequisites for the full flow

- The **Tabula** board running (see [docs/tabula.md](../docs/tabula.md)).
  Default `http://localhost:9955`, override with the `TABULA_API_URL` environment variable.
  Tabula supports SQLite (default, zero external dependencies) and PostgreSQL.
- The project you work on should have a **`CLAUDE.md`** describing the stack, repos,
  commands, and environments.
- For ingest from Jira/Confluence you need the **Atlassian MCP** configured in Claude Code.
