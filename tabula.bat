@echo off
setlocal
title Tabula

REM Si posiziona nella cartella dello script (dove sta il docker-compose.yml)
cd /d "%~dp0"

echo ============================================
echo            Avvio di Tabula
echo ============================================
echo.

REM Verifica che Docker sia installato e in esecuzione
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERRORE] Docker non e' raggiungibile.
    echo Avvia Docker Desktop e riprova.
    echo.
    pause
    exit /b 1
)

echo Costruzione delle immagini e avvio dei container...
echo (la prima volta puo' richiedere qualche minuto)
echo.

docker compose up --build -d
if errorlevel 1 (
    echo.
    echo [ERRORE] Avvio dei container fallito.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Tabula e' attivo!
echo    Interfaccia : http://localhost:5173
echo    API / docs  : http://localhost:9955/docs
echo ============================================
echo.

REM Apre il browser sull'interfaccia
start "" http://localhost:5173

echo Per fermare Tabula esegui:  stop-tabula.bat
echo.
pause
