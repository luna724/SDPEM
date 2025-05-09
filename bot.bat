@echo off

cd /d I:/SDPEM
call ./.venv/Scripts/activate
python pem_jsk.py
pause