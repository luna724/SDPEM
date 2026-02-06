python -m venv .venv
call .venv\Scripts\activate.bat

pip install -r requirements.txt

rem ifnude などの依存関係で再インストールされた onnxruntime (CPU版) を再度削除
pip uninstall -y onnxruntime

python setup.py

echo ----------------------
echo please update environments.json5 with your sd-webui path
echo Setup completed. you can now run launch.bat to start the application.
pause