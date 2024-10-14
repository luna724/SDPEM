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

rem Update pip
python -m pip install --upgrade pip