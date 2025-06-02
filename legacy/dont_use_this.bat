call ./.venv/Scripts/activate


set PYTHON_ARGS=--no_bert --no_fasttext --no_gensim --luna_theme --nojsk

python webui.py %PYTHON_ARGS%
pause