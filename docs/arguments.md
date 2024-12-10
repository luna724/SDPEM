| 引数名          | 型   | 必須 | デフォルト | 説明                    |
|-----------------|------|----|-------|-----------------------|
| `--noLM`, `-nolm` | bool | No | False | 全モデルの読み込みを無効化         |
| `--no_bert`     | bool | No | False | BERTモデルの読み込みを無効化      |
| `--no_fasttext` | bool | No | False | FastTextモデルの読み込みを無効化  |
| `--no_gensim`   | bool | No | False | Gensimモデルの読み込みを無効化    |
| `--no_booru`    | bool | No | False | Deepbooruモデルの読み込みを無効化 |
| `--luna_theme`  | bool | No | False | luna724.cssの読み込みを有効化  |
| `--half_booru`  | bool | No | False | Deepbooruモデルのhalf化    |
| `--ignore_cuda` | bool | No | False | CUDA有効チェックを無効化        |
| `--nojsk`       | bool | No | False | Jishakuを無効化           |
| `--nogpt2`      | bool | No | False | GPT-2の読み込みを無効化        |
| `--high_vram`   | bool | No | False | モデルを常にVRAMに読みこむ       |
| `--cpu`         | bool | No | False | モデルの実行にGPUを使わない       |