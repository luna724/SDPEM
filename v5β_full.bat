@echo off
set PYTHON_ARGS=--luna_theme --norpc

rem DON'T EDIT FROM BELOW
:venv
if exist venv (
    goto :pip_ins
) else (
    python -m venv .venv
)
:pip_ins
pip3 install -U jishaku
call ./.venv/Scripts/activate
python -m pip install --upgrade pip setuptools
pip install -r requirements.txt
pip install torch==2.1.2 torchvision==0.16.2 --extra-index-url https://download.pytorch.org/whl/cu121
python webui.py %PYTHON_ARGS%

pause