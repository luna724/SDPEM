# modules/database
[Agents](このファイルは編集しないでください)

## 目的
- AならBの確率(Cooccurence)
- AならBはありえない (Cooccurenceより信憑性の高い絶対的ルール)
- AとBは類似後 (無意味なプロンプトの羅列を避ける)
- Aを使うと rating: .. になりやすい
- LoRA C は A に関連がある
これらの要素を満たすNNではないプロンプト作成モデル、またはWord2Vecのようなベクトル空間モデルを構築する

[ok]はユーザーにより確認、承認、または作成されたもの

## preprocessing.py [ok]
- PreProcessor: 既存の画像データを元に、Inference用の統計データを作成するクラス

## matrix.py [ok]
- CooccurrenceMatrix: 渡されたタグ郡に対し、Aがある時、Bが出る確率を定義し、それを元に類似プロンプトを作成する

## conflict.py
- ConflictMap: AとBはありえない (Cooccurenceより信憑性の高い絶対的ルール)

