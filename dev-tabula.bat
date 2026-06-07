@echo off
setlocal
title Tabula - sviluppo (hot-reload)

cd /d "%~dp0"

echo ============================================
echo      Tabula - modalita' SVILUPPO
echo      (hot-reload backend + frontend)
echo ============================================
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Docker non e' raggiungibile.
    echo Avvia Docker Desktop e riprova.
    echo.
    pause
    exit /b 1
)

echo Avvio dei container in modalita' sviluppo...
echo (la prima volta puo' richiedere qualche minuto)
echo.

docker compose -f docker-compose.dev.yml up --build -d
if errorlevel 1 (
    echo.
    echo [ERRORE] Avvio fallito.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Tabula DEV e' attivo (hot-reload ON)
echo    Interfaccia : http://localhost:5173
echo    API / docs  : http://localhost:9955/docs
echo ============================================
echo.
echo Modifica i file in .\backend o .\frontend: le modifiche
echo vengono applicate automaticamente, senza riavviare.
echo.

start "" http://localhost:5173

echo Ora mostro i log (Ctrl+C chiude SOLO i log, i container restano attivi).
echo Per fermare i container esegui:  stop-tabula.bat
echo.
pause

docker compose -f docker-compose.dev.yml logs -f
