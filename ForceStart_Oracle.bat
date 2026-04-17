@echo off
echo =============================================
echo  ZetaFin: FORCE START ORACLE BACKEND
echo =============================================
set KEY="d:\finance product\frontend\public\ssh-key-2026-04-03 (1).key"
set IP=140.245.219.55
set REMOTE=/home/ubuntu/zetafin-backend

echo Killing any leftovers...
ssh -o StrictHostKeyChecking=no -i %KEY% ubuntu@%IP% "pkill -9 -f uvicorn ; echo done"

echo.
echo Starting backend...
ssh -o StrictHostKeyChecking=no -i %KEY% ubuntu@%IP% "bash -c 'cd /home/ubuntu/zetafin-backend && source venv/bin/activate && nohup uvicorn main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 & sleep 5 && echo STARTED && ps aux | grep uvicorn | grep -v grep'"

echo.
echo Checking log...
ssh -o StrictHostKeyChecking=no -i %KEY% ubuntu@%IP% "tail -n 20 /home/ubuntu/zetafin-backend/app.log"

echo.
echo =============================================
echo DONE. Check zetafin.app now.
echo =============================================
timeout /t 90
