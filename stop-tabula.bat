@echo off
setlocal
title Tabula - stop

cd /d "%~dp0"

echo Arresto dei container di Tabula...
docker compose -f docker-compose.dev.yml down
docker compose down

echo.
echo Tabula e' stato fermato. (Il database e' conservato nel volume "tabula-data".)
echo.
pause
