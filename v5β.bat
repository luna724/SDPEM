@echo off
:venv
if exist venv (
    goto :pip_ins
) else (
    python -m venv .venv
)
:pip_ins
call ./.venv/Scripts/activate
python -m pip install --upgrade pip setuptools
pip install -r requirements.txt
pip install torch==2.1.2 torchvision==0.16.2 --extra-index-url https://download.pytorch.org/whl/cu121


rem ARGUMENTS HERE / 引数設定場所
python webui.py


pause