call ./.venv/Scripts/activate


set PYTHON_ARGS=--no_bert --no_fasttext --no_gensim --luna_theme --server_ip 7866

python webui.py %PYTHON_ARGS%
pause