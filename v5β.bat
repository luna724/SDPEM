@echo off
:venv
if exist venv (
    goto :pip_ins
) else (
    python -m venv .venv
)

rem Install Requirements.txt
:pip_ins
call ./.venv/Scripts/activate
pip install -r requirements.txt
pip install torch==2.1.2 torchvision==0.16.2 --extra-index-url https://download.pytorch.org/whl/cu121

rem Update pip
python -m pip install --upgrade pip


python webui.py

pause