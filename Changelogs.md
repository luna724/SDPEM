# v4 What's new?
追加された要素は以下の通りです。
- PEM / PDB 用の launcher を追加

変更、バージョン変更された要素は以下の通りです
- [Prompt Resizer]: v1 -> v2 (+ 名前変更 -> Prompt finalizer)
- [Prompt finalizer v2]: 全体的なコードの書き直し
- [Character Exchanger]: v3 -> v3.01 -> v3.02
- [Character Exchanger v3.01]: クラス化に対応、各バージョンの呼び出しを可能に (大幅な変更がある場合に限る)
- [Character Exchanger v3.02]: v4変数に対応
- [Generate/Template]: v4 -> v4.1
- [Generate/Template v4.1]:  テンプレリスト更新後、displayName ではなく辞書のキーが表示される問題を修正
- [Generate/Template json v4.0.0 (10)]:
1. 新しい値を追加
   ```md
   - ["Values"]["NSFW_Prompt"]
   - ["Example"]["Other"]
   - ["Buildins"]["refiner"]
   ```
2. 値の変更
   ```md
   - ["Example"]["face"] -> List[str]
   - ["Example"]["location"] -> List[str]
   - ["Example"]["Headers"] -> List[str]
3. 値の削除
   ```md
   - ["Regional_Prompter"]
   - ["Example"]["lower"]
   - ["Example"]["face2"]
   - ["Example"]["location2"]
   ```
- [Generate/Template LoRA json v5]: 
1. 値の追加
   ```md
   - ["lora_variables"]
   ```
- [Generate/Template LoRA json]: v4 -> v5
- [Generate/Template json]: v3.2 -> v4.0.0
- [Generate/Template]: LoRA Variablesを実装
- [Generate/Template]: v4.0.0以下のjsonサポートを削除
- [Generate/Template]: v2以下の LoRA json サポートを削除
- [Generate/Template]: `$FACE2`, `$LOCATION2`を廃止 (変数は未廃止)
- [Generate/Template]: 変数の型を `$LORA` 等から ?AnyLoRA に変更。v2を除くすべての過去の値も引き続き使用可能 

| Old (v1) | Old (v2) | Legacy (v3) | New (v4) |
| --- | --- | --- | --- |
| %LORA% | %LORA:{Weight} | $LORA | ?AnyLoRA (via: $$LORA) |
| %CH_NAME% | None | $NAME | ?AnyName (via: $$NAME) |
| %CH_PROMPT% | None | $PROMPT | ?AnyPrompt (via: $$_PROMPT) |
| None | None | None | ?AnyExtend (via: $EXTEND, $$EXTEND) |
| %FACE% | None | $FACE | $FACE (via: ?AnyFace) |
| %LOCATION% | None | $LOCATION | $LOCATION (via: ?AnyLocation) |
| None | None | None | $ACCESSORY (via: ?AnyAccessory) |
| None | None | None | $OTHER (via: ?AnyOtherVariable) |
| None | None | None | $LV1 (via: ?AnyLV1) |
| None | None | None | $LV2 (via: ?AnyLV2) |

- [Generate/Tempalte]: ビルドイン変数のショートカットを作成可能に (現在 config.json でのみ)
- [Generate/Template]: 2つの変数を定義可能、4つの変数を設定可能に
- [Geneaate/Template]: [Beta] 一つのテンプレートに設定できるプロンプトスタイルを追加
- [Generate/Template]: Negative, ADetailer Prompt にビルドインキーワードを設定可能に
- [Generate/Template v4.0.0]: Regional Prompter のサポートを終了
- [Define/LoRA v5]: v4 -> v5
- [Generate/Template LoRA json]: いくつかの値を追加
1. 値の追加
   ```md
   - ["loraisLoRA"]
   ```
- [Generate/LoRA v5]: LV1, LV2 のセーブ機能を追加
- [Generate/LoRA v5]: $LoRA Trigger に LoRA ID 以外を入れたことを明記する変数を追加
- [Generate/LoRA v5]: $LoRA Trigger の値のチェック機能を追加
- [Generate/LoRA v5]: Load関数の対応バージョンを変更 (v2~v4 -> v4~v5)
- [Generate/LoRA v5]: Load機能による上書きが行われた際に、draftを保存する機能を削除 (プリントアウトに変更)
- [Generate/LoRA v5]: LoRA ID is LoRA が保持する値を変更 (bool -> bool|null)
- [Generate/Template]: v5 LoRA json に対応
- [Character Exchanger v3.03]: v5 LoRA json に部分的対応
- [Generate/Template]: v5 LoRA json を選択した際に KeyError が起こる問題を修正