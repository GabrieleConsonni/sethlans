<#
  Installa il toolkit Sethlans nella home globale di Claude Code (~/.claude).
  Copia il command /sethlans, i subagent generici e il protocollo Tabula.

  Uso:
    pwsh ./install.ps1            # copia (chiede conferma se sovrascrive)
    pwsh ./install.ps1 -Force     # sovrascrive senza chiedere
#>
param([switch]$Force)

$ErrorActionPreference = 'Stop'
$src = $PSScriptRoot
$dest = Join-Path $env:USERPROFILE '.claude'

Write-Host "Installazione toolkit Sethlans -> $dest" -ForegroundColor Cyan

# cartelle di destinazione
New-Item -ItemType Directory -Force -Path (Join-Path $dest 'commands') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $dest 'agents')   | Out-Null

function Copy-Item-Safe($from, $to) {
    if ((Test-Path $to) -and -not $Force) {
        Write-Host "  esiste gia: $to (usa -Force per sovrascrivere) - salto" -ForegroundColor Yellow
        return
    }
    Copy-Item $from $to -Force
    Write-Host "  copiato: $to" -ForegroundColor Green
}

Copy-Item-Safe (Join-Path $src 'commands\sethlans.md') (Join-Path $dest 'commands\sethlans.md')
Copy-Item-Safe (Join-Path $src 'tabula-protocol.md')   (Join-Path $dest 'tabula-protocol.md')

Get-ChildItem (Join-Path $src 'agents') -Filter *.md | ForEach-Object {
    Copy-Item-Safe $_.FullName (Join-Path $dest "agents\$($_.Name)")
}

Write-Host "Fatto. Riavvia Claude Code e digita /sethlans per usarlo." -ForegroundColor Cyan
