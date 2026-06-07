# Sethlans toolkit — orchestrazione di subagent su Tabula

Questa cartella è il cuore di [Sethlans](../README.md): la configurazione **globale** di
Claude Code che fa girare il flusso PO→UX→architect→dev, visualizzato sulla board
[Tabula](../docs/tabula.md):

```
claude-config/
├── commands/
│   └── sethlans.md        # il command /sethlans (l'orchestratore)
├── agents/                # i 10 subagent generici (riusabili su qualsiasi progetto)
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
├── tabula-protocol.md     # contratto API della board (citato da command + agent)
├── install.ps1            # installer Windows/PowerShell
└── install.sh             # installer macOS/Linux
```

## Come funziona

- **`/sethlans`** è l'orchestratore: ingest della richiesta (chiave Jira, link
  Confluence o descrizione libera), poi coordina i subagent fase per fase e riflette
  lo stato sulla board Tabula via HTTP.
- I **subagent sono generici**: non assumono un progetto specifico. La specifica del
  repo su cui lavorano la leggono dal `CLAUDE.md` del progetto corrente.
- **`tabula-protocol.md`** è la single source of truth dell'integrazione con la board
  (base URL, modello dati, enum di `status`/`phase`, ricette PowerShell). Command e
  agent lo referenziano invece di duplicare le ricette.

## Installazione

Questi file devono vivere nella home globale di Claude Code (`~/.claude/`), non nel
repo. Gli script li copiano al posto giusto.

**Windows / PowerShell**
```powershell
cd claude-config
pwsh ./install.ps1          # aggiungi -Force per sovrascrivere
```

**macOS / Linux**
```bash
cd claude-config
chmod +x install.sh
./install.sh                # aggiungi --force per sovrascrivere
```

Dopo l'installazione, **riavvia Claude Code** e digita `/sethlans <richiesta>`.

## Prerequisiti per il flusso completo

- La board **Tabula** in esecuzione (vedi [docs/tabula.md](../docs/tabula.md)).
  Default `http://localhost:9955`, override con la variabile d'ambiente `TABULA_API_URL`.
- Il progetto su cui lavori dovrebbe avere un **`CLAUDE.md`** che descrive stack, repo,
  comandi e ambienti: è da lì che i subagent generici si orientano.
- Per l'ingest da Jira/Confluence serve l'**MCP Atlassian** configurato in Claude Code.

## Nota sui path

`commands/sethlans.md` e `tabula-protocol.md` contengono alcuni riferimenti d'ambiente
(es. il path locale del backend Tabula e i riferimenti `~/.claude/...`). Sono pensati
per la macchina di sviluppo originale: se il tuo setup differisce, adatta quei
riferimenti dopo l'installazione.
