python -m venv .venv
call .venv\Scripts\activate.bat

pip install torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
pip uninstall -y onnxruntime

python setup.py

echo ----------------------
echo please update environments.json5 with your sd-webui path
echo Setup completed. you can now run launch.bat to start the application.
pause