@REM if not (exist .venv) (
@REM     echo please run setup.bat first.
@REM     pause
@REM     exit /b
@REM )

call .venv/scripts/activate
python webui.py %*