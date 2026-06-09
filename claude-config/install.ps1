<#
  Installs the Sethlans toolkit into Claude Code's global home (~/.claude).
  Copies the /sethlans skill, the generic subagents, and the Tabula protocol.
  Source of truth: ../.claude-plugin/ (plugin directory).

  Usage:
    pwsh ./install.ps1            # copy (prompts for confirmation if overwriting)
    pwsh ./install.ps1 -Force     # overwrite without prompting

  Preferred: use the Claude Code plugin system instead:
    /plugin install sethlans@claude-community
#>
param([switch]$Force)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$src  = Join-Path $repoRoot '.claude-plugin'
$dest = Join-Path $env:USERPROFILE '.claude'

Write-Host "Installing Sethlans toolkit -> $dest" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path (Join-Path $dest 'commands') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dest 'agents')   | Out-Null

function Copy-Item-Safe($from, $to) {
    if ((Test-Path $to) -and -not $Force) {
        Write-Host "  already exists: $to (use -Force to overwrite) - skipping" -ForegroundColor Yellow
        return
    }
    Copy-Item $from $to -Force
    Write-Host "  copied: $to" -ForegroundColor Green
}

Copy-Item-Safe (Join-Path $src 'skills\sethlans.md') (Join-Path $dest 'commands\sethlans.md')
Copy-Item-Safe (Join-Path $src 'tabula-protocol.md') (Join-Path $dest 'tabula-protocol.md')

Get-ChildItem (Join-Path $src 'agents') -Filter *.md | ForEach-Object {
    Copy-Item-Safe $_.FullName (Join-Path $dest "agents\$($_.Name)")
}

Write-Host "Done. Restart Claude Code and type /sethlans to use it." -ForegroundColor Cyan
