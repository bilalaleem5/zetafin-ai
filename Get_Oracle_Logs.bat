@echo off
echo ==================================================
echo   ZetaFin AI: LOG RETRIEVAL
echo ==================================================
echo.

set KEY="d:\finance product\frontend\public\ssh-key-2026-04-03 (1).key"
set IP=140.245.219.55
set REMOTE_PATH=/home/ubuntu/zetafin-backend

echo Fetching last 50 lines of app.log...
ssh -o StrictHostKeyChecking=no -i %KEY% ubuntu@%IP% "tail -n 50 %REMOTE_PATH%/app.log"

echo.
echo --------------------------------------------------
echo Window will stay open for 60 seconds...
echo --------------------------------------------------
timeout /t 60
