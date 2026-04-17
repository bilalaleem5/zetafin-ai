@echo off
echo ==================================================
echo   ZetaFin AI: FINAL DIRECT DEPLOYMENT (SCP)
echo ==================================================
echo.

set KEY="d:\finance product\frontend\public\ssh-key-2026-04-03 (1).key"
set IP=140.245.219.55
set REMOTE_PATH=/home/ubuntu/zetafin-backend

echo Connecting to Oracle (%IP%)...
echo Sending AI Intelligence files...

scp -o StrictHostKeyChecking=no -i %KEY% "d:\finance product\backend\database.py" ubuntu@%IP%:%REMOTE_PATH%/database.py
scp -o StrictHostKeyChecking=no -i %KEY% "d:\finance product\backend\ai_consultant.py" ubuntu@%IP%:%REMOTE_PATH%/ai_consultant.py
scp -o StrictHostKeyChecking=no -i %KEY% "d:\finance product\backend\models.py" ubuntu@%IP%:%REMOTE_PATH%/models.py
scp -o StrictHostKeyChecking=no -i %KEY% "d:\finance product\backend\main.py" ubuntu@%IP%:%REMOTE_PATH%/main.py

echo.
echo Restarting Backend Application...
ssh -o StrictHostKeyChecking=no -i %KEY% ubuntu@%IP% "pkill -f uvicorn ; sleep 2 ; cd %REMOTE_PATH% && nohup ./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &"

echo.
echo --------------------------------------------------
echo DONE! Login/Signup should now work PERFECTLY.
echo Test it at https://zetafin.app
echo Window will stay open for 60 seconds...
echo --------------------------------------------------
timeout /t 60
