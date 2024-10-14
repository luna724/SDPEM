# SDPEM/addons
ここには SDPEM に対するアドオンを導入できます

## 拡張機能が認識される形式
- 必要(必須ではない): `/metadata.json`, `init.py`

#### /metadata.json
```json
{
  "init": "init.py",
  "author": []
}
```
これらはキーが存在しない場合、デフォルト値が使用される <br>

`init`: 初期化時に読み込まれるファイル。デフォルト: `init.py` <br>
`author`: `Extensions`タブの Author の値に使用される。 デフォルト: `[]`


#### 


`PEM v4b ` 現在、拡張機能は以下の機能をサポートします
また、この拡張機能システムの構造は変わる可能性しかありません

| trigger file | trigger | trigger file key (in /metadata.json) |
| --- | --- | --- |
| `/generate.py:finish` | when finish Generate | "generate.py:finish": ["generate.py", "finish"] |

## generate.py:finish
生成終了時に outputs の値すべてを渡される
引数例

```py
def finish(**got):
  print(got)

->

{
  "prompt": "", "negative": "", "ad_prompt": "", "ad_negative": ""
}
```