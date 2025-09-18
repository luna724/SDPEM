@echo off
call .venv/scripts/activate
python webui.py --ui_port 24000 --api_port 23999 --debug

pause