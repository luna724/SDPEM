python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
python setup.py

echo "----------------------"
echo "please update environments.json5 with your sd-webui path"
echo "Setup completed. you can now run launch.bat to start the application."
pause