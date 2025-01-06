@echo off
set PYTHON_ARGS=--nolm --nojsk --luna_theme --norpc

rem DON'T EDIT FROM BELOW
:venv
if exist venv (
    echo "must needed launch v5β-full.bat once."
    pause
    exit
) else (
    python -m venv .venv
)
:pip_ins
call ./.venv/Scripts/activate
python webui.py %PYTHON_ARGS%

pause